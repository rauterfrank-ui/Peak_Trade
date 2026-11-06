"""CURRENT Productive Activation policy v1 — singular semantic authority.

Productive Activation = admission of the already-governed productive runtime path to operate
inside its existing bounded, fail-closed, PRE_EXTERNAL envelope.

RUNTIME_AUTHORIZATION_EFFECT=PRODUCTIVE_RUNTIME_ADMISSION_ONLY
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1 import (
    consumer_wiring_authorized_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    AUTONOMY_CAN_MINT_PERMIT,
    AUTONOMY_CAN_POST,
    FULL_CORE_AUTONOMY_AUTHORITY_BOUNDARY,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    CONTINUOUS_RUN_AUTHORIZED,
)
from src.ops.p5_10_productive_activation_and_binding_v1.constants_v1 import (
    P5_AUTHORITY_CUTOVER_AUTHORIZED,
    PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED,
)

POLICY_OWNER: Final[str] = "governance.current_productive_activation_policy_v1"
SCHEMA_VERSION: Final[str] = "current_productive_activation_policy/v1"
POLICY_ID: Final[str] = "CURRENT_PRODUCTIVE_ACTIVATION_POLICY_V1"
WORKPACKAGE_ID: Final[str] = "CURRENT_PRODUCTIVE_ACTIVATION_POLICY_V1"
NORMATIVE_SPEC: Final[str] = "docs/ops/specs/CURRENT_PRODUCTIVE_ACTIVATION_POLICY_V1.md"
POLICY_RECORD_CONFIG: Final[str] = (
    "config/governance/current_productive_activation_policy_v1_record.json"
)
OWNER_GO_DECISION_CONFIG: Final[str] = (
    "config/governance/current_productive_activation_policy_owner_go_v1_decision.json"
)

BASELINE_ORIGIN_MAIN_SHA: Final[str] = "958657754033f432dc723fc4f56412f2de9430dd"
RATIFIED_F1_M9_THRESHOLD_SECONDS: Final[int] = 600
RATIFIED_F1_M9_THRESHOLD_DIGEST: Final[str] = (
    "e556ea63f68df3651cf38ef4d49d675f94a0e20f67c5b72f9044f9492b9bf109"
)
BOUND_APPLY_OWNER_RECORD_DIGEST: Final[str] = (
    "3f0895951d0708d017326a8b4f779c433d609d09d67459fe47f1239f214a2f95"
)

RUNTIME_ADMISSION_ENVELOPE: Final[str] = "BOUNDED_PRE_EXTERNAL_PRODUCTIVE_RUNTIME"
RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE: Final[str] = (
    "F1_M9_THRESHOLD_CONSUMER_HARDENING_V2_BRIDGE"
)
RUNTIME_SURFACE_F1_M9_INTEGRATED_OFFLINE_REPLAY: Final[str] = (
    "F1_M9_THRESHOLD_CONSUMER_INTEGRATED_OFFLINE_REPLAY"
)
ADMITTED_RUNTIME_SURFACES: Final[tuple[str, ...]] = (
    RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
    RUNTIME_SURFACE_F1_M9_INTEGRATED_OFFLINE_REPLAY,
)

BOUND_FORENSIC_REVIEW_DECISION: Final[str] = (
    "config/governance/productive_activation_boundary_forensic_review_v1_decision_v1.json"
)
BOUND_F1_M9_CONSUMER_WIRING_DECISION: Final[str] = (
    "config/governance/"
    "governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1_decision_v1.json"
)
BOUND_F1_M9_APPLY_START_DECISION: Final[str] = (
    "config/governance/"
    "governed_f1_m9_scoped_owner_productive_runtime_apply_start_real_mechanical_continuation_v1_decision_v1.json"
)

STATUS_POLICY_VALID: Final[str] = "PRODUCTIVE_ACTIVATION_POLICY_VALID"
STATUS_POLICY_DENIED: Final[str] = "PRODUCTIVE_ACTIVATION_POLICY_DENIED_FAIL_CLOSED"
STATUS_ADMISSION_GRANTED: Final[str] = "PRODUCTIVE_RUNTIME_ADMISSION_GRANTED"
STATUS_ADMISSION_DENIED: Final[str] = "PRODUCTIVE_RUNTIME_ADMISSION_DENIED_FAIL_CLOSED"

CONTINUOUS_RUN_AUTHORIZED_BY_POLICY: Final[bool] = False
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
class ProductiveActivationPolicyValidationResultV1:
    policy_status: str
    policy_authorized: bool
    policy_record_digest: str | None
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProductiveRuntimeAdmissionResultV1:
    admission_status: str
    runtime_admission_granted: bool
    productive_activation_authorized: bool
    runtime_surface: str | None
    policy_record_digest: str | None
    reason_codes: tuple[str, ...]
    continuous_run_authorized: bool
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


def _decision_digest(root: Path, rel: str) -> str | None:
    payload = _load_json(root, rel)
    if not payload:
        return None
    return compute_content_sha256(payload)


def load_productive_activation_policy_record_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _REPO_ROOT
    return _load_json(root, POLICY_RECORD_CONFIG)


def canonical_policy_record_body_v1(record: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key != "policy_record_digest"}


def validate_productive_activation_policy_record_v1(
    *, repo_root: Path | None = None
) -> ProductiveActivationPolicyValidationResultV1:
    root = repo_root or _REPO_ROOT
    reasons: list[str] = []
    record = load_productive_activation_policy_record_v1(repo_root=root)
    if not record:
        return ProductiveActivationPolicyValidationResultV1(
            policy_status=STATUS_POLICY_DENIED,
            policy_authorized=False,
            policy_record_digest=None,
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
    if record.get("runtime_admission_envelope") != RUNTIME_ADMISSION_ENVELOPE:
        reasons.append("RUNTIME_ADMISSION_ENVELOPE_MISMATCH")

    surfaces = record.get("admitted_runtime_surfaces")
    if not isinstance(surfaces, list) or tuple(surfaces) != ADMITTED_RUNTIME_SURFACES:
        reasons.append("ADMITTED_RUNTIME_SURFACES_MISMATCH")

    non_impl = record.get("explicit_non_implications")
    if not isinstance(non_impl, dict):
        reasons.append("EXPLICIT_NON_IMPLICATIONS_MISSING")
    else:
        for key, expected in (
            ("continuous_run_authorized", False),
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
    if not isinstance(lineage, dict):
        reasons.append("BOUND_LINEAGE_MISSING")
    else:
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
        for rel_key, rel_path in (
            ("forensic_review_decision_config", BOUND_FORENSIC_REVIEW_DECISION),
            ("f1_m9_consumer_wiring_decision_config", BOUND_F1_M9_CONSUMER_WIRING_DECISION),
            ("f1_m9_runtime_apply_start_decision_config", BOUND_F1_M9_APPLY_START_DECISION),
        ):
            if lineage.get(rel_key) != rel_path:
                reasons.append(f"LINEAGE_PATH_{rel_key.upper()}")
            bound_digest = str(lineage.get(f"{rel_key}_digest") or "")
            actual_digest = _decision_digest(root, rel_path)
            if not actual_digest or bound_digest != actual_digest:
                reasons.append(f"LINEAGE_DIGEST_{rel_key.upper()}")

    owner = _load_json(root, OWNER_GO_DECISION_CONFIG)
    if owner.get("current_productive_activation_policy_owner_go") is not True:
        reasons.append("OWNER_GO_DECISION_NOT_CONSUMED")

    authorized = not reasons and record.get("policy_authorized") is True
    return ProductiveActivationPolicyValidationResultV1(
        policy_status=STATUS_POLICY_VALID if authorized else STATUS_POLICY_DENIED,
        policy_authorized=authorized,
        policy_record_digest=computed_digest if is_valid_sha256_hex(computed_digest) else None,
        reason_codes=tuple(dict.fromkeys(reasons)),
    )


def standing_productive_activation_authorized_v1(*, repo_root: Path | None = None) -> bool:
    return validate_productive_activation_policy_record_v1(repo_root=repo_root).policy_authorized


def evaluate_productive_runtime_admission_v1(
    *,
    runtime_surface: str,
    repo_root: Path | None = None,
) -> ProductiveRuntimeAdmissionResultV1:
    """Fail-closed runtime admission; never implies continuous run or external effect."""
    root = repo_root or _REPO_ROOT
    policy = validate_productive_activation_policy_record_v1(repo_root=root)
    reasons = list(policy.reason_codes)

    if runtime_surface not in ADMITTED_RUNTIME_SURFACES:
        reasons.append("RUNTIME_SURFACE_NOT_ADMITTED")

    if not consumer_wiring_authorized_v1(repo_root=root):
        reasons.append("F1_M9_CONSUMER_WIRING_NOT_AUTHORIZED")

    granted = policy.policy_authorized is True and not reasons
    return ProductiveRuntimeAdmissionResultV1(
        admission_status=STATUS_ADMISSION_GRANTED if granted else STATUS_ADMISSION_DENIED,
        runtime_admission_granted=granted,
        productive_activation_authorized=granted,
        runtime_surface=runtime_surface,
        policy_record_digest=policy.policy_record_digest,
        reason_codes=tuple(dict.fromkeys(reasons)),
        continuous_run_authorized=CONTINUOUS_RUN_AUTHORIZED_BY_POLICY,
        external_effect_authorized=EXTERNAL_EFFECT_AUTHORIZED_BY_POLICY,
        post_allowed=POST_ALLOWED_BY_POLICY,
        wire_send_permitted=WIRE_SEND_PERMITTED_BY_POLICY,
        real_venue_post_allowed=REAL_VENUE_POST_ALLOWED_BY_POLICY,
        autonomy_can_mint_permit=AUTONOMY_CAN_MINT_PERMIT_BY_POLICY,
        autonomy_can_post=AUTONOMY_CAN_POST_BY_POLICY,
        credential_access_performed=CREDENTIAL_ACCESS_PERFORMED_BY_POLICY,
    )


def prove_p5_bind_does_not_imply_productive_activation_v1() -> bool:
    """P5.10 layered bind enabled is not global Productive Activation policy authority."""
    if PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED is not True:
        return False
    if P5_AUTHORITY_CUTOVER_AUTHORIZED is not False:
        return False
    return standing_productive_activation_authorized_v1() is True


def prove_downstream_authorities_independent_v1() -> bool:
    if CONTINUOUS_RUN_AUTHORIZED is not False:
        return False
    if AUTONOMY_CAN_MINT_PERMIT is not False:
        return False
    if AUTONOMY_CAN_POST is not False:
        return False
    if FULL_CORE_AUTONOMY_AUTHORITY_BOUNDARY != (
        "ONE_CYCLE_ORCHESTRATION_TO_PRE_EXTERNAL_EFFECT_ONLY"
    ):
        return False
    return True


__all__ = [
    "ADMITTED_RUNTIME_SURFACES",
    "BASELINE_ORIGIN_MAIN_SHA",
    "BOUNDED_ORCHESTRATION_TERMINAL",
    "CONTINUOUS_RUN_AUTHORIZED_BY_POLICY",
    "CREDENTIAL_ACCESS_PERFORMED_BY_POLICY",
    "EXTERNAL_EFFECT_AUTHORIZED_BY_POLICY",
    "NORMATIVE_SPEC",
    "OWNER_GO_DECISION_CONFIG",
    "POLICY_ID",
    "POLICY_OWNER",
    "POLICY_RECORD_CONFIG",
    "POST_ALLOWED_BY_POLICY",
    "RATIFIED_F1_M9_THRESHOLD_DIGEST",
    "RATIFIED_F1_M9_THRESHOLD_SECONDS",
    "REAL_VENUE_POST_ALLOWED_BY_POLICY",
    "RUNTIME_ADMISSION_ENVELOPE",
    "RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE",
    "RUNTIME_SURFACE_F1_M9_INTEGRATED_OFFLINE_REPLAY",
    "SCHEMA_VERSION",
    "STATUS_ADMISSION_DENIED",
    "STATUS_ADMISSION_GRANTED",
    "STATUS_POLICY_DENIED",
    "STATUS_POLICY_VALID",
    "WIRE_SEND_PERMITTED_BY_POLICY",
    "WORKPACKAGE_ID",
    "ProductiveActivationPolicyValidationResultV1",
    "ProductiveRuntimeAdmissionResultV1",
    "canonical_policy_record_body_v1",
    "evaluate_productive_runtime_admission_v1",
    "load_productive_activation_policy_record_v1",
    "prove_downstream_authorities_independent_v1",
    "prove_p5_bind_does_not_imply_productive_activation_v1",
    "standing_productive_activation_authorized_v1",
    "validate_productive_activation_policy_record_v1",
]
