"""CURRENT Continuous Run policy v1 — singular semantic authority.

Continuous Run = governed repeated invocation of the already-authorized bounded
productive runtime cycle, where every iteration independently re-enters through
CURRENT admission and safety gates and every iteration remains terminally bounded
at PRE_EXTERNAL_EFFECT_BOUNDARY.

RUNTIME_AUTHORIZATION_EFFECT=CONTINUOUS_RUNTIME_ADMISSION_ONLY
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.current_productive_activation_policy_v1 import (
    ADMITTED_RUNTIME_SURFACES,
    CONTINUOUS_RUN_AUTHORIZED_BY_POLICY as PRODUCTIVE_POLICY_CONTINUOUS_RUN_FALSE,
    POLICY_RECORD_CONFIG as PRODUCTIVE_ACTIVATION_POLICY_RECORD_CONFIG,
    RATIFIED_F1_M9_THRESHOLD_DIGEST,
    RATIFIED_F1_M9_THRESHOLD_SECONDS,
    BOUND_APPLY_OWNER_RECORD_DIGEST,
    canonical_policy_record_body_v1 as canonical_productive_activation_body_v1,
    load_productive_activation_policy_record_v1,
    standing_productive_activation_authorized_v1,
    validate_productive_activation_policy_record_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    CONTINUOUS_RUN_AUTHORIZED as ORCHESTRATOR_CONTINUOUS_RUN_MODULE_PIN,
    PRIMARY_SEMANTIC_IDENTITY as TARGET_ORCHESTRATOR_IDENTITY,
)

POLICY_OWNER: Final[str] = "governance.current_continuous_run_policy_v1"
SCHEMA_VERSION: Final[str] = "current_continuous_run_policy/v1"
POLICY_ID: Final[str] = "CURRENT_CONTINUOUS_RUN_POLICY_V1"
WORKPACKAGE_ID: Final[str] = "CURRENT_CONTINUOUS_RUN_POLICY_V1"
NORMATIVE_SPEC: Final[str] = "docs/ops/specs/CURRENT_CONTINUOUS_RUN_POLICY_V1.md"
POLICY_RECORD_CONFIG: Final[str] = "config/governance/current_continuous_run_policy_v1_record.json"
OWNER_GO_DECISION_CONFIG: Final[str] = (
    "config/governance/current_continuous_run_policy_owner_go_v1_decision.json"
)

BASELINE_ORIGIN_MAIN_SHA: Final[str] = "79a8b581e66346b7d40cf402cbc8f1f05f156678"
TARGET_ORCHESTRATOR_MODULE: Final[str] = (
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_governed_continuous_cycle_orchestrator_v1.py"
)
TARGET_RUNTIME_BINDING_MODULE: Final[str] = (
    "src/governance/current_continuous_run_runtime_binding_v1.py"
)
ORCHESTRATION_ENVELOPE: Final[str] = "BOUNDED_PRE_EXTERNAL_CONTINUOUS_PRODUCTIVE_CYCLES"
TARGET_ORCHESTRATOR_SURFACE: Final[str] = "GOVERNED_CONTINUOUS_CYCLE_ORCHESTRATOR_V1"

STATUS_POLICY_VALID: Final[str] = "CONTINUOUS_RUN_POLICY_VALID"
STATUS_POLICY_DENIED: Final[str] = "CONTINUOUS_RUN_POLICY_DENIED_FAIL_CLOSED"
STATUS_ADMISSION_GRANTED: Final[str] = "CONTINUOUS_RUNTIME_ADMISSION_GRANTED"
STATUS_ADMISSION_DENIED: Final[str] = "CONTINUOUS_RUNTIME_ADMISSION_DENIED_FAIL_CLOSED"

EXTERNAL_EFFECT_AUTHORIZED_BY_POLICY: Final[bool] = False
POST_ALLOWED_BY_POLICY: Final[bool] = False
REAL_VENUE_POST_ALLOWED_BY_POLICY: Final[bool] = False
WIRE_SEND_PERMITTED_BY_POLICY: Final[bool] = False
AUTONOMY_CAN_MINT_PERMIT_BY_POLICY: Final[bool] = False
AUTONOMY_CAN_POST_BY_POLICY: Final[bool] = False
CREDENTIAL_ACCESS_PERFORMED_BY_POLICY: Final[bool] = False

BOUNDED_ORCHESTRATION_TERMINAL: Final[str] = "PRE_EXTERNAL_EFFECT_BOUNDARY"

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class ContinuousRunPolicyValidationResultV1:
    policy_status: str
    policy_authorized: bool
    policy_record_digest: str | None
    productive_activation_policy_digest: str | None
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ContinuousRuntimeAdmissionResultV1:
    admission_status: str
    continuous_runtime_admission_granted: bool
    continuous_run_authorized: bool
    productive_activation_authorized: bool
    productive_runtime_admission: bool
    runtime_surface: str | None
    policy_record_digest: str | None
    productive_activation_policy_digest: str | None
    reason_codes: tuple[str, ...]
    external_effect_authorized: bool
    post_allowed: bool
    wire_send_permitted: bool
    real_venue_post_allowed: bool
    autonomy_can_mint_permit: bool
    autonomy_can_post: bool
    credential_access_performed: bool


def _load_json(root: Path, rel: str) -> dict[str, Any]:
    path = root / rel
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def load_continuous_run_policy_record_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _REPO_ROOT
    return _load_json(root, POLICY_RECORD_CONFIG)


def canonical_policy_record_body_v1(record: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key != "policy_record_digest"}


def _productive_activation_record_digest(root: Path) -> str | None:
    record = load_productive_activation_policy_record_v1(repo_root=root)
    if not record:
        return None
    body = canonical_productive_activation_body_v1(record)
    return compute_content_sha256(body)


def validate_continuous_run_policy_record_v1(
    *,
    repo_root: Path | None = None,
    orchestrator_target: str | None = None,
) -> ContinuousRunPolicyValidationResultV1:
    root = repo_root or _REPO_ROOT
    reasons: list[str] = []
    record = load_continuous_run_policy_record_v1(repo_root=root)
    if not record:
        return ContinuousRunPolicyValidationResultV1(
            policy_status=STATUS_POLICY_DENIED,
            policy_authorized=False,
            policy_record_digest=None,
            productive_activation_policy_digest=None,
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
    if record.get("policy_authorized") is not True:
        reasons.append("POLICY_NOT_AUTHORIZED")
    if record.get("baseline_origin_main_sha") != BASELINE_ORIGIN_MAIN_SHA:
        reasons.append("BASELINE_SHA_MISMATCH")
    if record.get("orchestration_envelope") != ORCHESTRATION_ENVELOPE:
        reasons.append("ORCHESTRATION_ENVELOPE_MISMATCH")
    if record.get("target_orchestrator_surface") != TARGET_ORCHESTRATOR_SURFACE:
        reasons.append("TARGET_ORCHESTRATOR_SURFACE_MISMATCH")
    if record.get("target_orchestrator_module") != TARGET_ORCHESTRATOR_MODULE:
        reasons.append("TARGET_ORCHESTRATOR_MODULE_MISMATCH")
    if record.get("target_runtime_binding_module") != TARGET_RUNTIME_BINDING_MODULE:
        reasons.append("TARGET_RUNTIME_BINDING_MODULE_MISMATCH")

    target = orchestrator_target or TARGET_ORCHESTRATOR_SURFACE
    if target != record.get("target_orchestrator_surface"):
        reasons.append("ORCHESTRATOR_TARGET_MISMATCH")

    surfaces = record.get("admitted_runtime_surfaces")
    if not isinstance(surfaces, list) or tuple(surfaces) != ADMITTED_RUNTIME_SURFACES:
        reasons.append("ADMITTED_RUNTIME_SURFACES_MISMATCH")

    non_impl = record.get("explicit_non_implications")
    if not isinstance(non_impl, dict):
        reasons.append("EXPLICIT_NON_IMPLICATIONS_MISSING")
    else:
        for key, expected in (
            ("external_effect_authorized", False),
            ("post_allowed", False),
            ("wire_send_permitted", False),
            ("real_venue_post_allowed", False),
            ("autonomy_can_mint_permit", False),
            ("autonomy_can_post", False),
            ("credential_access_performed", False),
        ):
            if non_impl.get(key) is not expected:
                reasons.append(f"NON_IMPLICATION_{key.upper()}")

    lineage = record.get("bound_lineage")
    pa_digest: str | None = None
    if not isinstance(lineage, dict):
        reasons.append("BOUND_LINEAGE_MISSING")
    else:
        if lineage.get("productive_activation_policy_record_config") != (
            PRODUCTIVE_ACTIVATION_POLICY_RECORD_CONFIG
        ):
            reasons.append("PRODUCTIVE_ACTIVATION_POLICY_PATH_MISMATCH")
        pa_digest = _productive_activation_record_digest(root)
        bound_pa = str(lineage.get("productive_activation_policy_record_digest") or "")
        if not pa_digest or bound_pa != pa_digest:
            reasons.append("PRODUCTIVE_ACTIVATION_POLICY_DIGEST_MISMATCH")
        if int(lineage.get("ratified_threshold_numeric_max_age_seconds", -1)) != (
            RATIFIED_F1_M9_THRESHOLD_SECONDS
        ):
            reasons.append("F1_M9_THRESHOLD_VALUE_MISMATCH")
        if (
            str(lineage.get("owner_threshold_record_digest") or "")
            != RATIFIED_F1_M9_THRESHOLD_DIGEST
        ):
            reasons.append("F1_M9_THRESHOLD_DIGEST_MISMATCH")
        if str(lineage.get("authorized_owner_apply_record_digest") or "") != (
            BOUND_APPLY_OWNER_RECORD_DIGEST
        ):
            reasons.append("F1_M9_APPLY_OWNER_DIGEST_MISMATCH")

    if not standing_productive_activation_authorized_v1(repo_root=root):
        reasons.append("PRODUCTIVE_ACTIVATION_PREREQUISITE_INVALID")

    activation_policy = validate_productive_activation_policy_record_v1(repo_root=root)
    if activation_policy.policy_authorized is not True:
        reasons.append("PRODUCTIVE_ACTIVATION_POLICY_DENIED")

    owner = _load_json(root, OWNER_GO_DECISION_CONFIG)
    if owner.get("current_continuous_run_policy_owner_go") is not True:
        reasons.append("OWNER_GO_DECISION_NOT_CONSUMED")

    authorized = not reasons and record.get("policy_authorized") is True
    return ContinuousRunPolicyValidationResultV1(
        policy_status=STATUS_POLICY_VALID if authorized else STATUS_POLICY_DENIED,
        policy_authorized=authorized,
        policy_record_digest=computed_digest if is_valid_sha256_hex(computed_digest) else None,
        productive_activation_policy_digest=pa_digest,
        reason_codes=tuple(dict.fromkeys(reasons)),
    )


def standing_continuous_run_authorized_v1(*, repo_root: Path | None = None) -> bool:
    return validate_continuous_run_policy_record_v1(repo_root=repo_root).policy_authorized


def evaluate_continuous_runtime_admission_v1(
    *,
    runtime_surface: str,
    repo_root: Path | None = None,
    orchestrator_target: str | None = None,
) -> ContinuousRuntimeAdmissionResultV1:
    """Fail-closed continuous runtime admission; never implies external effect."""
    root = repo_root or _REPO_ROOT
    policy = validate_continuous_run_policy_record_v1(
        repo_root=root,
        orchestrator_target=orchestrator_target,
    )
    reasons = list(policy.reason_codes)

    if runtime_surface not in ADMITTED_RUNTIME_SURFACES:
        reasons.append("RUNTIME_SURFACE_NOT_ADMITTED")

    from src.governance.current_productive_activation_policy_v1 import (
        evaluate_productive_runtime_admission_v1,
    )

    productive = evaluate_productive_runtime_admission_v1(
        runtime_surface=runtime_surface,
        repo_root=root,
    )
    productive_granted = productive.runtime_admission_granted is True
    if not productive_granted:
        reasons.extend(list(productive.reason_codes) or ["PRODUCTIVE_RUNTIME_ADMISSION_DENIED"])

    granted = policy.policy_authorized is True and productive_granted and not reasons
    return ContinuousRuntimeAdmissionResultV1(
        admission_status=STATUS_ADMISSION_GRANTED if granted else STATUS_ADMISSION_DENIED,
        continuous_runtime_admission_granted=granted,
        continuous_run_authorized=granted,
        productive_activation_authorized=productive_granted
        and productive.productive_activation_authorized,
        productive_runtime_admission=productive_granted,
        runtime_surface=runtime_surface,
        policy_record_digest=policy.policy_record_digest,
        productive_activation_policy_digest=policy.productive_activation_policy_digest,
        reason_codes=tuple(dict.fromkeys(reasons)),
        external_effect_authorized=EXTERNAL_EFFECT_AUTHORIZED_BY_POLICY,
        post_allowed=POST_ALLOWED_BY_POLICY,
        wire_send_permitted=WIRE_SEND_PERMITTED_BY_POLICY,
        real_venue_post_allowed=REAL_VENUE_POST_ALLOWED_BY_POLICY,
        autonomy_can_mint_permit=AUTONOMY_CAN_MINT_PERMIT_BY_POLICY,
        autonomy_can_post=AUTONOMY_CAN_POST_BY_POLICY,
        credential_access_performed=CREDENTIAL_ACCESS_PERFORMED_BY_POLICY,
    )


def prove_productive_activation_does_not_imply_continuous_run_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or _REPO_ROOT
    if not standing_productive_activation_authorized_v1(repo_root=root):
        return False
    if PRODUCTIVE_POLICY_CONTINUOUS_RUN_FALSE is not False:
        return False
    from src.governance.current_productive_activation_policy_v1 import (
        evaluate_productive_runtime_admission_v1,
        RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
    )

    admission = evaluate_productive_runtime_admission_v1(
        runtime_surface=RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
        repo_root=root,
    )
    return admission.continuous_run_authorized is False


def prove_continuous_run_does_not_imply_external_effect_v1() -> bool:
    if EXTERNAL_EFFECT_AUTHORIZED_BY_POLICY is True:
        return False
    if POST_ALLOWED_BY_POLICY is True:
        return False
    if WIRE_SEND_PERMITTED_BY_POLICY is True:
        return False
    if ORCHESTRATOR_CONTINUOUS_RUN_MODULE_PIN is not False:
        return False
    return True


def prove_orchestrator_target_identity_v1() -> bool:
    return TARGET_ORCHESTRATOR_IDENTITY == "governed_continuous_cycle_orchestrator_v1"


__all__ = [
    "BASELINE_ORIGIN_MAIN_SHA",
    "BOUNDED_ORCHESTRATION_TERMINAL",
    "ContinuousRunPolicyValidationResultV1",
    "ContinuousRuntimeAdmissionResultV1",
    "NORMATIVE_SPEC",
    "OWNER_GO_DECISION_CONFIG",
    "POLICY_ID",
    "POLICY_OWNER",
    "POLICY_RECORD_CONFIG",
    "TARGET_ORCHESTRATOR_MODULE",
    "TARGET_ORCHESTRATOR_SURFACE",
    "TARGET_RUNTIME_BINDING_MODULE",
    "WORKPACKAGE_ID",
    "canonical_policy_record_body_v1",
    "evaluate_continuous_runtime_admission_v1",
    "load_continuous_run_policy_record_v1",
    "prove_continuous_run_does_not_imply_external_effect_v1",
    "prove_orchestrator_target_identity_v1",
    "prove_productive_activation_does_not_imply_continuous_run_v1",
    "standing_continuous_run_authorized_v1",
    "validate_continuous_run_policy_record_v1",
]
