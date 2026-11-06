"""Standing External Effect Lift policy v1 — singular semantic authority.

Governed lift grants standing external-effect admission at the Full-Core gate seam
when lineage-bound records validate. Does **not** authorize permit mint, credential
access, venue POST, or autonomy POST.

RUNTIME_AUTHORIZATION_EFFECT=STANDING_EXTERNAL_EFFECT_LIFT_ONLY
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.external_effect_authorization_policy_v1 import (
    POLICY_RECORD_CONFIG as EXTERNAL_EFFECT_AUTHORIZATION_POLICY_RECORD_CONFIG,
    canonical_policy_record_body_v1 as canonical_external_effect_authorization_body_v1,
    standing_external_effect_authorization_policy_authorized_v1,
    validate_external_effect_authorization_policy_record_v1,
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
from src.ops.full_core_live_path_composition_root_v1.external_effect_gate_v1 import (
    ExternalEffectDecisionV1,
    evaluate_external_effect_v1,
)
from src.ops.pre_external_to_external_effect_boundary_bounded_wp_v1.proof_v1 import (
    prove_pre_external_to_external_effect_boundary_v1,
)

POLICY_OWNER: Final[str] = "governance.standing_external_effect_lift_policy_v1"
SCHEMA_VERSION: Final[str] = "standing_external_effect_lift_policy/v1"
POLICY_ID: Final[str] = "STANDING_EXTERNAL_EFFECT_LIFT_POLICY_V1"
WORKPACKAGE_ID: Final[str] = "STANDING_EXTERNAL_EFFECT_LIFT_POLICY_V1"
NORMATIVE_SPEC: Final[str] = "docs/ops/specs/STANDING_EXTERNAL_EFFECT_LIFT_POLICY_V1.md"
POLICY_RECORD_CONFIG: Final[str] = (
    "config/governance/standing_external_effect_lift_policy_v1_record.json"
)
OWNER_GO_DECISION_CONFIG: Final[str] = (
    "config/governance/standing_external_effect_lift_owner_go_v1_decision.json"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/standing_external_effect_lift_policy_v1_decision_v1.json"
)

BASELINE_ORIGIN_MAIN_SHA: Final[str] = "2309dbd5b04a2fc2b41d88d9905d96671e51b1e3"

LIFT_ENVELOPE: Final[str] = "GOVERNED_STANDING_EXTERNAL_EFFECT_GATE_LIFT"
TARGET_GATE_MODULE: Final[str] = (
    "src/ops/full_core_live_path_composition_root_v1/external_effect_gate_v1.py"
)
TARGET_ENVELOPE_SEAM_MODULE: Final[str] = (
    "src/ops/full_core_live_path_composition_root_v1/envelope_bound_external_effect_send_seam_v1.py"
)
TARGET_LIFT_GATE_BINDING_MODULE: Final[str] = (
    "src/governance/standing_external_effect_lift_gate_binding_v1.py"
)
BOUND_EXTERNAL_EFFECT_AUTHORIZATION_POLICY_RECORD_DIGEST: Final[str] = (
    "4fa8b5b34077d568d3575f83e1ad21e295e09d3bb7bf90a0b42e5631924653d0"
)

STATUS_POLICY_VALID: Final[str] = "STANDING_EXTERNAL_EFFECT_LIFT_POLICY_VALID"
STATUS_POLICY_DENIED: Final[str] = "STANDING_EXTERNAL_EFFECT_LIFT_POLICY_DENIED_FAIL_CLOSED"
STATUS_LIFT_GRANTED: Final[str] = "STANDING_EXTERNAL_EFFECT_LIFT_GRANTED"
STATUS_LIFT_DENIED: Final[str] = "STANDING_EXTERNAL_EFFECT_LIFT_DENIED_FAIL_CLOSED"

STANDING_EXTERNAL_EFFECT_LIFT_BY_POLICY: Final[bool] = True
PERMIT_MINT_AUTHORIZED_BY_POLICY: Final[bool] = False
CREDENTIAL_ACCESS_PERFORMED_BY_POLICY: Final[bool] = False
POST_ALLOWED_BY_POLICY: Final[bool] = False
REAL_VENUE_POST_ALLOWED_BY_POLICY: Final[bool] = False
AUTONOMY_CAN_MINT_PERMIT_BY_POLICY: Final[bool] = False
AUTONOMY_CAN_POST_BY_POLICY: Final[bool] = False

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class StandingExternalEffectLiftPolicyValidationResultV1:
    policy_status: str
    lift_policy_authorized: bool
    policy_record_digest: str | None
    external_effect_authorization_policy_digest: str | None
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StandingExternalEffectLiftAdmissionResultV1:
    admission_status: str
    standing_external_effect_lift_granted: bool
    governed_standing_external_effect_authorized: bool
    external_effect_authorization_policy_authorized: bool
    pre_external_boundary_proven: bool
    gate_decision: ExternalEffectDecisionV1 | None
    policy_record_digest: str | None
    reason_codes: tuple[str, ...]
    import_time_standing_constant: bool
    post_allowed: bool
    real_venue_post_allowed: bool
    permit_mint_authorized: bool
    credential_access_performed: bool
    autonomy_can_mint_permit: bool
    autonomy_can_post: bool


def _load_json(root: Path, rel: str) -> dict[str, Any]:
    path = root / rel
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def load_standing_external_effect_lift_policy_record_v1(
    *, repo_root: Path | None = None
) -> dict[str, Any]:
    root = repo_root or _REPO_ROOT
    return _load_json(root, POLICY_RECORD_CONFIG)


def canonical_policy_record_body_v1(record: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key != "policy_record_digest"}


def _authorization_policy_digest(root: Path) -> str | None:
    record = _load_json(root, EXTERNAL_EFFECT_AUTHORIZATION_POLICY_RECORD_CONFIG)
    if not record:
        return None
    return compute_content_sha256(canonical_external_effect_authorization_body_v1(record))


def validate_standing_external_effect_lift_policy_record_v1(
    *, repo_root: Path | None = None
) -> StandingExternalEffectLiftPolicyValidationResultV1:
    root = repo_root or _REPO_ROOT
    reasons: list[str] = []
    record = load_standing_external_effect_lift_policy_record_v1(repo_root=root)
    if not record:
        return StandingExternalEffectLiftPolicyValidationResultV1(
            policy_status=STATUS_POLICY_DENIED,
            lift_policy_authorized=False,
            policy_record_digest=None,
            external_effect_authorization_policy_digest=None,
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
    if record.get("standing_external_effect_lift_authorized") is not True:
        reasons.append("LIFT_NOT_AUTHORIZED_IN_RECORD")
    if record.get("baseline_origin_main_sha") != BASELINE_ORIGIN_MAIN_SHA:
        reasons.append("BASELINE_SHA_MISMATCH")
    if record.get("lift_envelope") != LIFT_ENVELOPE:
        reasons.append("LIFT_ENVELOPE_MISMATCH")
    if record.get("target_gate_module") != TARGET_GATE_MODULE:
        reasons.append("GATE_MODULE_MISMATCH")
    if record.get("target_envelope_seam_module") != TARGET_ENVELOPE_SEAM_MODULE:
        reasons.append("ENVELOPE_SEAM_MODULE_MISMATCH")
    if record.get("target_lift_gate_binding_module") != TARGET_LIFT_GATE_BINDING_MODULE:
        reasons.append("LIFT_GATE_BINDING_MODULE_MISMATCH")

    non_impl = record.get("explicit_non_implications")
    if not isinstance(non_impl, dict):
        reasons.append("EXPLICIT_NON_IMPLICATIONS_MISSING")
    else:
        for key, expected in (
            ("permit_mint_authorized", False),
            ("credential_access_performed", False),
            ("post_allowed", False),
            ("real_venue_post_allowed", False),
            ("autonomy_can_mint_permit", False),
            ("autonomy_can_post", False),
        ):
            if non_impl.get(key) is not expected:
                reasons.append(f"NON_IMPLICATION_{key.upper()}")

    auth_digest: str | None = None
    lineage = record.get("bound_lineage")
    if not isinstance(lineage, dict):
        reasons.append("BOUND_LINEAGE_MISSING")
    else:
        if lineage.get("external_effect_authorization_policy_record_config") != (
            EXTERNAL_EFFECT_AUTHORIZATION_POLICY_RECORD_CONFIG
        ):
            reasons.append("EXTERNAL_EFFECT_AUTHORIZATION_POLICY_PATH_MISMATCH")
        auth_digest = _authorization_policy_digest(root)
        bound_auth = str(lineage.get("external_effect_authorization_policy_record_digest") or "")
        if not auth_digest or bound_auth != auth_digest:
            reasons.append("EXTERNAL_EFFECT_AUTHORIZATION_POLICY_DIGEST_MISMATCH")
        if bound_auth != BOUND_EXTERNAL_EFFECT_AUTHORIZATION_POLICY_RECORD_DIGEST:
            reasons.append("EXTERNAL_EFFECT_AUTHORIZATION_POLICY_DIGEST_CONSTANT_MISMATCH")

    if not standing_external_effect_authorization_policy_authorized_v1(repo_root=root):
        reasons.append("EXTERNAL_EFFECT_AUTHORIZATION_POLICY_PREREQUISITE_INVALID")
    if (
        validate_external_effect_authorization_policy_record_v1(repo_root=root).policy_authorized
        is not True
    ):
        reasons.append("EXTERNAL_EFFECT_AUTHORIZATION_POLICY_DENIED")

    owner = _load_json(root, OWNER_GO_DECISION_CONFIG)
    if owner.get("standing_external_effect_lift_owner_go") is not True:
        reasons.append("OWNER_GO_DECISION_NOT_CONSUMED")

    authorized = not reasons and record.get("standing_external_effect_lift_authorized") is True
    return StandingExternalEffectLiftPolicyValidationResultV1(
        policy_status=STATUS_POLICY_VALID if authorized else STATUS_POLICY_DENIED,
        lift_policy_authorized=authorized,
        policy_record_digest=computed_digest if is_valid_sha256_hex(computed_digest) else None,
        external_effect_authorization_policy_digest=auth_digest,
        reason_codes=tuple(dict.fromkeys(reasons)),
    )


def standing_external_effect_lift_granted_v1(*, repo_root: Path | None = None) -> bool:
    return (
        validate_standing_external_effect_lift_policy_record_v1(
            repo_root=repo_root
        ).lift_policy_authorized
        is True
    )


def governed_standing_external_effect_authorized_v1(*, repo_root: Path | None = None) -> bool:
    """True only when lift policy + external-effect authorization policy both validate."""
    root = repo_root or _REPO_ROOT
    return standing_external_effect_lift_granted_v1(repo_root=root) and (
        standing_external_effect_authorization_policy_authorized_v1(repo_root=root) is True
    )


def evaluate_standing_external_effect_lift_admission_v1(
    *, repo_root: Path | None = None
) -> StandingExternalEffectLiftAdmissionResultV1:
    root = repo_root or _REPO_ROOT
    policy = validate_standing_external_effect_lift_policy_record_v1(repo_root=root)
    reasons = list(policy.reason_codes)

    pre_external = prove_pre_external_to_external_effect_boundary_v1()
    pre_external_ok = pre_external.ok is True
    if not pre_external_ok:
        reasons.append("PRE_EXTERNAL_BOUNDARY_PROOF_FAILED")

    gate: ExternalEffectDecisionV1 | None = None
    governed_standing = False
    if policy.lift_policy_authorized and pre_external_ok:
        gate = evaluate_external_effect_v1(standing_external_effect_authorized=True)
        governed_standing = gate.external_effect_authorized is True
        if not governed_standing:
            reasons.append("GATE_STANDING_LIFT_NOT_ADMITTED")
        if EXTERNAL_EFFECT_AUTHORIZED is True:
            reasons.append("IMPORT_TIME_STANDING_CONSTANT_MUST_REMAIN_FALSE")

    granted = (
        policy.lift_policy_authorized is True
        and pre_external_ok
        and governed_standing
        and not reasons
    )
    return StandingExternalEffectLiftAdmissionResultV1(
        admission_status=STATUS_LIFT_GRANTED if granted else STATUS_LIFT_DENIED,
        standing_external_effect_lift_granted=granted,
        governed_standing_external_effect_authorized=governed_standing,
        external_effect_authorization_policy_authorized=standing_external_effect_authorization_policy_authorized_v1(
            repo_root=root
        ),
        pre_external_boundary_proven=pre_external_ok,
        gate_decision=gate,
        policy_record_digest=policy.policy_record_digest,
        reason_codes=tuple(dict.fromkeys(reasons)),
        import_time_standing_constant=EXTERNAL_EFFECT_AUTHORIZED is True,
        post_allowed=POST_ALLOWED_BY_POLICY,
        real_venue_post_allowed=REAL_VENUE_POST_ALLOWED_BY_POLICY,
        permit_mint_authorized=PERMIT_MINT_AUTHORIZED_BY_POLICY,
        credential_access_performed=CREDENTIAL_ACCESS_PERFORMED_BY_POLICY,
        autonomy_can_mint_permit=AUTONOMY_CAN_MINT_PERMIT_BY_POLICY,
        autonomy_can_post=AUTONOMY_CAN_POST_BY_POLICY,
    )


def prove_lift_does_not_authorize_permit_mint_v1() -> bool:
    return PERMIT_MINT_AUTHORIZED_BY_POLICY is False and AUTONOMY_CAN_MINT_PERMIT is False


def prove_lift_does_not_authorize_credential_access_v1() -> bool:
    return CREDENTIAL_ACCESS_PERFORMED_BY_POLICY is False


def prove_lift_does_not_authorize_real_venue_post_v1() -> bool:
    if POST_ALLOWED_BY_POLICY is True or REAL_VENUE_POST_ALLOWED_BY_POLICY is True:
        return False
    if POST_ALLOWED is not False or REAL_VENUE_POST_ALLOWED is not False:
        return False
    if AUTONOMY_CAN_POST is not False:
        return False
    return True


def prove_import_time_standing_constant_unchanged_v1() -> bool:
    return EXTERNAL_EFFECT_AUTHORIZED is False


__all__ = [
    "BASELINE_ORIGIN_MAIN_SHA",
    "DECISION_CONFIG",
    "LIFT_ENVELOPE",
    "NORMATIVE_SPEC",
    "OWNER_GO_DECISION_CONFIG",
    "POLICY_ID",
    "POLICY_OWNER",
    "POLICY_RECORD_CONFIG",
    "STANDING_EXTERNAL_EFFECT_LIFT_BY_POLICY",
    "StandingExternalEffectLiftAdmissionResultV1",
    "StandingExternalEffectLiftPolicyValidationResultV1",
    "WORKPACKAGE_ID",
    "canonical_policy_record_body_v1",
    "evaluate_standing_external_effect_lift_admission_v1",
    "governed_standing_external_effect_authorized_v1",
    "load_standing_external_effect_lift_policy_record_v1",
    "prove_import_time_standing_constant_unchanged_v1",
    "prove_lift_does_not_authorize_credential_access_v1",
    "prove_lift_does_not_authorize_permit_mint_v1",
    "prove_lift_does_not_authorize_real_venue_post_v1",
    "standing_external_effect_lift_granted_v1",
    "validate_standing_external_effect_lift_policy_record_v1",
]
