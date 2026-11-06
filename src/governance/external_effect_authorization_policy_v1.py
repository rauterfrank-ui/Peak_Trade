"""External Effect authorization policy v1 — singular semantic authority.

External Effect authorization policy = governed semantic contract for crossing the
PRE_EXTERNAL → standing Full-Core external-effect gate seam. Policy authorization
binds lineage and admission evaluators; it does **not** lift standing
EXTERNAL_EFFECT_AUTHORIZED, permit mint, credential access, or venue POST flags.

RUNTIME_AUTHORIZATION_EFFECT=EXTERNAL_EFFECT_POLICY_ADMISSION_ONLY
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.current_continuous_run_policy_v1 import (
    POLICY_RECORD_CONFIG as CONTINUOUS_RUN_POLICY_RECORD_CONFIG,
    canonical_policy_record_body_v1 as canonical_continuous_run_body_v1,
    standing_continuous_run_authorized_v1,
    validate_continuous_run_policy_record_v1,
)
from src.governance.current_productive_activation_policy_v1 import (
    POLICY_RECORD_CONFIG as PRODUCTIVE_ACTIVATION_POLICY_RECORD_CONFIG,
    canonical_policy_record_body_v1 as canonical_productive_activation_body_v1,
    standing_productive_activation_authorized_v1,
    validate_productive_activation_policy_record_v1,
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

POLICY_OWNER: Final[str] = "governance.external_effect_authorization_policy_v1"
SCHEMA_VERSION: Final[str] = "external_effect_authorization_policy/v1"
POLICY_ID: Final[str] = "EXTERNAL_EFFECT_AUTHORIZATION_POLICY_V1"
WORKPACKAGE_ID: Final[str] = "EXTERNAL_EFFECT_AUTHORIZATION_POLICY_V1"
NORMATIVE_SPEC: Final[str] = "docs/ops/specs/EXTERNAL_EFFECT_AUTHORIZATION_POLICY_V1.md"
POLICY_RECORD_CONFIG: Final[str] = (
    "config/governance/external_effect_authorization_policy_v1_record.json"
)
OWNER_GO_DECISION_CONFIG: Final[str] = (
    "config/governance/external_effect_authorization_policy_owner_go_v1_decision.json"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/external_effect_authorization_policy_v1_decision_v1.json"
)

BASELINE_ORIGIN_MAIN_SHA: Final[str] = "b5e0fd94bbf7ba5f1742c98086e548d450ab4d2b"

AUTHORIZATION_ENVELOPE: Final[str] = "PRE_EXTERNAL_TO_STANDING_EXTERNAL_EFFECT_GATE_POLICY"
TARGET_EXTERNAL_EFFECT_GATE_MODULE: Final[str] = (
    "src/ops/full_core_live_path_composition_root_v1/external_effect_gate_v1.py"
)
TARGET_ENVELOPE_SEND_SEAM_MODULE: Final[str] = (
    "src/ops/full_core_live_path_composition_root_v1/envelope_bound_external_effect_send_seam_v1.py"
)
TARGET_GATE_BINDING_MODULE: Final[str] = (
    "src/governance/external_effect_authorization_policy_gate_binding_v1.py"
)
BOUND_FORENSIC_REVIEW_DECISION: Final[str] = (
    "config/governance/external_effect_boundary_forensic_review_v1_decision_v1.json"
)
BOUND_PRE_EXTERNAL_BOUNDARY_SPEC: Final[str] = (
    "docs/ops/specs/PRE_EXTERNAL_TO_EXTERNAL_EFFECT_BOUNDARY_BOUNDED_WP_V1.md"
)
BOUND_FORENSIC_REVIEW_DECISION_DIGEST: Final[str] = (
    "fe077e1fe5da497a84f2219b801ab9037fe539f685ce33a055a5a956e3e930ed"
)

STATUS_POLICY_VALID: Final[str] = "EXTERNAL_EFFECT_AUTHORIZATION_POLICY_VALID"
STATUS_POLICY_DENIED: Final[str] = "EXTERNAL_EFFECT_AUTHORIZATION_POLICY_DENIED_FAIL_CLOSED"
STATUS_ADMISSION_GRANTED: Final[str] = "EXTERNAL_EFFECT_POLICY_ADMISSION_GRANTED"
STATUS_ADMISSION_DENIED: Final[str] = "EXTERNAL_EFFECT_POLICY_ADMISSION_DENIED_FAIL_CLOSED"

STANDING_EXTERNAL_EFFECT_AUTHORIZED_BY_POLICY: Final[bool] = False
POST_ALLOWED_BY_POLICY: Final[bool] = False
REAL_VENUE_POST_ALLOWED_BY_POLICY: Final[bool] = False
WIRE_SEND_PERMITTED_BY_POLICY: Final[bool] = False
AUTONOMY_CAN_MINT_PERMIT_BY_POLICY: Final[bool] = False
AUTONOMY_CAN_POST_BY_POLICY: Final[bool] = False
CREDENTIAL_ACCESS_PERFORMED_BY_POLICY: Final[bool] = False
PERMIT_MINT_AUTHORIZED_BY_POLICY: Final[bool] = False

BOUNDARY_TERMINAL: Final[str] = "PRE_EXTERNAL_EFFECT_BOUNDARY"
GATE_SEAM: Final[str] = "STANDING_EXTERNAL_EFFECT_GATE_AND_ENVELOPE_SEAM"

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class ExternalEffectAuthorizationPolicyValidationResultV1:
    policy_status: str
    policy_authorized: bool
    policy_record_digest: str | None
    continuous_run_policy_digest: str | None
    productive_activation_policy_digest: str | None
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExternalEffectPolicyAdmissionResultV1:
    admission_status: str
    policy_admission_granted: bool
    external_effect_authorization_policy_authorized: bool
    productive_activation_authorized: bool
    continuous_run_authorized: bool
    pre_external_boundary_proven: bool
    gate_decision: ExternalEffectDecisionV1 | None
    policy_record_digest: str | None
    reason_codes: tuple[str, ...]
    standing_external_effect_authorized: bool
    post_allowed: bool
    wire_send_permitted: bool
    real_venue_post_allowed: bool
    autonomy_can_mint_permit: bool
    autonomy_can_post: bool
    credential_access_performed: bool
    permit_mint_authorized: bool


def _load_json(root: Path, rel: str) -> dict[str, Any]:
    path = root / rel
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def load_external_effect_authorization_policy_record_v1(
    *, repo_root: Path | None = None
) -> dict[str, Any]:
    root = repo_root or _REPO_ROOT
    return _load_json(root, POLICY_RECORD_CONFIG)


def canonical_policy_record_body_v1(record: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key != "policy_record_digest"}


def _record_digest(root: Path, rel: str, canonical: Any) -> str | None:
    record = _load_json(root, rel)
    if not record:
        return None
    body = canonical(record)
    return compute_content_sha256(body)


def validate_external_effect_authorization_policy_record_v1(
    *, repo_root: Path | None = None
) -> ExternalEffectAuthorizationPolicyValidationResultV1:
    root = repo_root or _REPO_ROOT
    reasons: list[str] = []
    record = load_external_effect_authorization_policy_record_v1(repo_root=root)
    if not record:
        return ExternalEffectAuthorizationPolicyValidationResultV1(
            policy_status=STATUS_POLICY_DENIED,
            policy_authorized=False,
            policy_record_digest=None,
            continuous_run_policy_digest=None,
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
    if record.get("authorization_envelope") != AUTHORIZATION_ENVELOPE:
        reasons.append("AUTHORIZATION_ENVELOPE_MISMATCH")
    if record.get("target_external_effect_gate_module") != TARGET_EXTERNAL_EFFECT_GATE_MODULE:
        reasons.append("GATE_MODULE_MISMATCH")
    if record.get("target_envelope_send_seam_module") != TARGET_ENVELOPE_SEND_SEAM_MODULE:
        reasons.append("ENVELOPE_SEAM_MODULE_MISMATCH")
    if record.get("target_gate_binding_module") != TARGET_GATE_BINDING_MODULE:
        reasons.append("GATE_BINDING_MODULE_MISMATCH")
    if record.get("gate_seam") != GATE_SEAM:
        reasons.append("GATE_SEAM_MISMATCH")
    if record.get("boundary_terminal") != BOUNDARY_TERMINAL:
        reasons.append("BOUNDARY_TERMINAL_MISMATCH")

    non_impl = record.get("explicit_non_implications")
    if not isinstance(non_impl, dict):
        reasons.append("EXPLICIT_NON_IMPLICATIONS_MISSING")
    else:
        for key, expected in (
            ("standing_external_effect_authorized", False),
            ("post_allowed", False),
            ("wire_send_permitted", False),
            ("real_venue_post_allowed", False),
            ("autonomy_can_mint_permit", False),
            ("autonomy_can_post", False),
            ("credential_access_performed", False),
            ("permit_mint_authorized", False),
        ):
            if non_impl.get(key) is not expected:
                reasons.append(f"NON_IMPLICATION_{key.upper()}")

    pa_digest: str | None = None
    cr_digest: str | None = None
    lineage = record.get("bound_lineage")
    if not isinstance(lineage, dict):
        reasons.append("BOUND_LINEAGE_MISSING")
    else:
        if lineage.get("productive_activation_policy_record_config") != (
            PRODUCTIVE_ACTIVATION_POLICY_RECORD_CONFIG
        ):
            reasons.append("PRODUCTIVE_ACTIVATION_POLICY_PATH_MISMATCH")
        pa_digest = _record_digest(
            root,
            PRODUCTIVE_ACTIVATION_POLICY_RECORD_CONFIG,
            canonical_productive_activation_body_v1,
        )
        bound_pa = str(lineage.get("productive_activation_policy_record_digest") or "")
        if not pa_digest or bound_pa != pa_digest:
            reasons.append("PRODUCTIVE_ACTIVATION_POLICY_DIGEST_MISMATCH")

        if (
            lineage.get("continuous_run_policy_record_config")
            != CONTINUOUS_RUN_POLICY_RECORD_CONFIG
        ):
            reasons.append("CONTINUOUS_RUN_POLICY_PATH_MISMATCH")
        cr_digest = _record_digest(
            root,
            CONTINUOUS_RUN_POLICY_RECORD_CONFIG,
            canonical_continuous_run_body_v1,
        )
        bound_cr = str(lineage.get("continuous_run_policy_record_digest") or "")
        if not cr_digest or bound_cr != cr_digest:
            reasons.append("CONTINUOUS_RUN_POLICY_DIGEST_MISMATCH")

        if lineage.get("external_effect_boundary_forensic_review_decision_config") != (
            BOUND_FORENSIC_REVIEW_DECISION
        ):
            reasons.append("FORENSIC_REVIEW_DECISION_PATH_MISMATCH")
        forensic_payload = _load_json(root, BOUND_FORENSIC_REVIEW_DECISION)
        if not forensic_payload:
            reasons.append("FORENSIC_REVIEW_DECISION_MISSING")
        else:
            forensic_digest = compute_content_sha256(forensic_payload)
            bound_forensic = str(
                lineage.get("external_effect_boundary_forensic_review_decision_digest") or ""
            )
            if bound_forensic != forensic_digest:
                reasons.append("FORENSIC_REVIEW_DECISION_DIGEST_MISMATCH")
            if bound_forensic != BOUND_FORENSIC_REVIEW_DECISION_DIGEST:
                reasons.append("FORENSIC_REVIEW_DECISION_DIGEST_CONSTANT_MISMATCH")
        if lineage.get("pre_external_boundary_spec") != BOUND_PRE_EXTERNAL_BOUNDARY_SPEC:
            reasons.append("PRE_EXTERNAL_SPEC_PATH_MISMATCH")

    if not standing_productive_activation_authorized_v1(repo_root=root):
        reasons.append("PRODUCTIVE_ACTIVATION_PREREQUISITE_INVALID")
    if not standing_continuous_run_authorized_v1(repo_root=root):
        reasons.append("CONTINUOUS_RUN_PREREQUISITE_INVALID")
    if (
        validate_productive_activation_policy_record_v1(repo_root=root).policy_authorized
        is not True
    ):
        reasons.append("PRODUCTIVE_ACTIVATION_POLICY_DENIED")
    if validate_continuous_run_policy_record_v1(repo_root=root).policy_authorized is not True:
        reasons.append("CONTINUOUS_RUN_POLICY_DENIED")

    owner = _load_json(root, OWNER_GO_DECISION_CONFIG)
    if owner.get("external_effect_authorization_policy_owner_go") is not True:
        reasons.append("OWNER_GO_DECISION_NOT_CONSUMED")

    authorized = not reasons and record.get("policy_authorized") is True
    return ExternalEffectAuthorizationPolicyValidationResultV1(
        policy_status=STATUS_POLICY_VALID if authorized else STATUS_POLICY_DENIED,
        policy_authorized=authorized,
        policy_record_digest=computed_digest if is_valid_sha256_hex(computed_digest) else None,
        continuous_run_policy_digest=cr_digest,
        productive_activation_policy_digest=pa_digest,
        reason_codes=tuple(dict.fromkeys(reasons)),
    )


def standing_external_effect_authorization_policy_authorized_v1(
    *, repo_root: Path | None = None
) -> bool:
    return (
        validate_external_effect_authorization_policy_record_v1(
            repo_root=repo_root
        ).policy_authorized
        is True
    )


def evaluate_external_effect_policy_admission_v1(
    *, repo_root: Path | None = None
) -> ExternalEffectPolicyAdmissionResultV1:
    """Fail-closed policy admission at PRE_EXTERNAL → gate seam; never lifts standing flags."""
    root = repo_root or _REPO_ROOT
    policy = validate_external_effect_authorization_policy_record_v1(repo_root=root)
    reasons = list(policy.reason_codes)

    pre_external = prove_pre_external_to_external_effect_boundary_v1()
    pre_external_ok = pre_external.ok is True
    if not pre_external_ok:
        reasons.append("PRE_EXTERNAL_BOUNDARY_PROOF_FAILED")

    gate = evaluate_external_effect_v1()
    if gate.external_effect_authorized is True or gate.venue_mutation_performed is True:
        reasons.append("STANDING_GATE_MUST_REMAIN_FAIL_CLOSED")
    if EXTERNAL_EFFECT_AUTHORIZED is True:
        reasons.append("STANDING_EXTERNAL_EFFECT_CONSTANT_DRIFT")

    granted = policy.policy_authorized is True and pre_external_ok and not reasons
    return ExternalEffectPolicyAdmissionResultV1(
        admission_status=STATUS_ADMISSION_GRANTED if granted else STATUS_ADMISSION_DENIED,
        policy_admission_granted=granted,
        external_effect_authorization_policy_authorized=granted,
        productive_activation_authorized=standing_productive_activation_authorized_v1(
            repo_root=root
        ),
        continuous_run_authorized=standing_continuous_run_authorized_v1(repo_root=root),
        pre_external_boundary_proven=pre_external_ok,
        gate_decision=gate,
        policy_record_digest=policy.policy_record_digest,
        reason_codes=tuple(dict.fromkeys(reasons)),
        standing_external_effect_authorized=STANDING_EXTERNAL_EFFECT_AUTHORIZED_BY_POLICY,
        post_allowed=POST_ALLOWED_BY_POLICY,
        wire_send_permitted=WIRE_SEND_PERMITTED_BY_POLICY,
        real_venue_post_allowed=REAL_VENUE_POST_ALLOWED_BY_POLICY,
        autonomy_can_mint_permit=AUTONOMY_CAN_MINT_PERMIT_BY_POLICY,
        autonomy_can_post=AUTONOMY_CAN_POST_BY_POLICY,
        credential_access_performed=CREDENTIAL_ACCESS_PERFORMED_BY_POLICY,
        permit_mint_authorized=PERMIT_MINT_AUTHORIZED_BY_POLICY,
    )


def prove_pre_external_reachability_does_not_imply_external_effect_authorization_v1() -> bool:
    pre = prove_pre_external_to_external_effect_boundary_v1()
    if pre.ok is not True:
        return False
    if STANDING_EXTERNAL_EFFECT_AUTHORIZED_BY_POLICY is True:
        return False
    if EXTERNAL_EFFECT_AUTHORIZED is not False:
        return False
    return True


def prove_policy_does_not_authorize_permit_mint_v1() -> bool:
    return PERMIT_MINT_AUTHORIZED_BY_POLICY is False and AUTONOMY_CAN_MINT_PERMIT is False


def prove_policy_does_not_authorize_credential_access_v1() -> bool:
    return CREDENTIAL_ACCESS_PERFORMED_BY_POLICY is False


def prove_policy_does_not_authorize_real_venue_post_v1() -> bool:
    if POST_ALLOWED_BY_POLICY is True:
        return False
    if REAL_VENUE_POST_ALLOWED_BY_POLICY is True:
        return False
    if POST_ALLOWED is not False:
        return False
    if REAL_VENUE_POST_ALLOWED is not False:
        return False
    if AUTONOMY_CAN_POST is not False:
        return False
    return True


def prove_standing_gate_chain_present_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or _REPO_ROOT
    paths = (
        TARGET_EXTERNAL_EFFECT_GATE_MODULE,
        TARGET_ENVELOPE_SEND_SEAM_MODULE,
        TARGET_GATE_BINDING_MODULE,
        BOUND_PRE_EXTERNAL_BOUNDARY_SPEC,
    )
    if not all((root / rel).is_file() for rel in paths):
        return False
    gate_text = (root / TARGET_EXTERNAL_EFFECT_GATE_MODULE).read_text(encoding="utf-8")
    seam_text = (root / TARGET_ENVELOPE_SEND_SEAM_MODULE).read_text(encoding="utf-8")
    return (
        "evaluate_external_effect_v1" in gate_text
        and "EXTERNAL_EFFECT_AUTHORIZED" in seam_text
        and "evaluate_external_effect_v1" in seam_text
    )


__all__ = [
    "AUTHORIZATION_ENVELOPE",
    "BASELINE_ORIGIN_MAIN_SHA",
    "BOUNDARY_TERMINAL",
    "DECISION_CONFIG",
    "ExternalEffectAuthorizationPolicyValidationResultV1",
    "ExternalEffectPolicyAdmissionResultV1",
    "GATE_SEAM",
    "NORMATIVE_SPEC",
    "OWNER_GO_DECISION_CONFIG",
    "POLICY_ID",
    "POLICY_OWNER",
    "POLICY_RECORD_CONFIG",
    "STANDING_EXTERNAL_EFFECT_AUTHORIZED_BY_POLICY",
    "TARGET_ENVELOPE_SEND_SEAM_MODULE",
    "TARGET_EXTERNAL_EFFECT_GATE_MODULE",
    "TARGET_GATE_BINDING_MODULE",
    "WORKPACKAGE_ID",
    "canonical_policy_record_body_v1",
    "evaluate_external_effect_policy_admission_v1",
    "load_external_effect_authorization_policy_record_v1",
    "prove_policy_does_not_authorize_credential_access_v1",
    "prove_policy_does_not_authorize_permit_mint_v1",
    "prove_policy_does_not_authorize_real_venue_post_v1",
    "prove_pre_external_reachability_does_not_imply_external_effect_authorization_v1",
    "prove_standing_gate_chain_present_v1",
    "standing_external_effect_authorization_policy_authorized_v1",
    "validate_external_effect_authorization_policy_record_v1",
]
