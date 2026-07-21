"""V7 Operator Clarification Authority — governance overlay over immutable prereg.

Not a second preregistration. Does not mutate the original V7 preregistration or
digest. Resolves implementation ambiguities B1–B6 only. Evaluation remains gated
by contract evaluation_authorized=false until a separate Operator-GO.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = (
    "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_OPERATOR_CLARIFICATION_AUTHORITY_V7=true"
)
AUTHORITY_REL_PATH = (
    "config/research/"
    "bollinger_mr_midband_exit_reentry_cooldown_operator_clarification_authority_v7.json"
)
AUTHORITY_ID = "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_OPERATOR_CLARIFICATION_AUTHORITY_V7"
AUTHORITY_VERSION = "v7.0.0"
SCHEMA_VERSION = "bollinger_mr_midband_exit_reentry_cooldown_operator_clarification_authority.v7"
HYPOTHESIS_ID = "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V7"
REQUIRED_PREREGISTRATION_DIGEST = "4e39138698628ea9d9ee7119050aba5d5398d765808878c4d26be3102d60e680"
OPERATOR_DECISIONS_STATUS = "OPERATOR_DECISIONS_RECORDED_IMPLEMENTATION_ONLY"
READY_STATUS = "READY_FOR_OPERATOR_EVALUATION_AUTHORIZATION"
ALLOWED_LIFECYCLE_STATES = (
    "DEFINITION_ONLY_PREREGISTERED",
    "OPERATOR_DECISIONS_RECORDED_IMPLEMENTATION_ONLY",
    "IMPLEMENTATION_WIRED_NOT_AUTHORIZED",
    "READY_FOR_OPERATOR_EVALUATION_AUTHORIZATION",
)
ALLOWED_TRANSITIONS = {
    ("DEFINITION_ONLY_PREREGISTERED", "OPERATOR_DECISIONS_RECORDED_IMPLEMENTATION_ONLY"),
    ("OPERATOR_DECISIONS_RECORDED_IMPLEMENTATION_ONLY", "IMPLEMENTATION_WIRED_NOT_AUTHORIZED"),
    ("IMPLEMENTATION_WIRED_NOT_AUTHORIZED", "READY_FOR_OPERATOR_EVALUATION_AUTHORIZATION"),
}
OWNER_MAP_REL_PATH = (
    "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)
WIRING_AUTH_REL_PATH = "config/governance/technical_canonical_wiring_authorization_v1.json"
OWNER_SURFACE = "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_OPERATOR_CLARIFICATION_AUTHORITY_V7"
B1_THROUGH_B6 = ("B1", "B2", "B3", "B4", "B5", "B6")


class OperatorClarificationAuthorityError(ValueError):
    """Fail-closed clarification-authority validation error."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def canonical_json_sha256(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def compute_authority_digest(authority: Mapping[str, Any]) -> str:
    body = {k: v for k, v in authority.items() if k != "authority_digest"}
    return canonical_json_sha256(body)


def load_authority(repo_root: Path | None = None) -> dict[str, Any]:
    repo = repo_root or _repo_root()
    path = repo / AUTHORITY_REL_PATH
    if not path.is_file():
        raise OperatorClarificationAuthorityError("MISSING_AUTHORITY")
    return json.loads(path.read_text(encoding="utf-8"))


def assert_transition_allowed(*, from_state: str, to_state: str) -> None:
    if from_state not in ALLOWED_LIFECYCLE_STATES or to_state not in ALLOWED_LIFECYCLE_STATES:
        raise OperatorClarificationAuthorityError(
            f"UNKNOWN_LIFECYCLE_STATE:{from_state}->{to_state}"
        )
    if from_state == to_state:
        return
    if (from_state, to_state) not in ALLOWED_TRANSITIONS:
        raise OperatorClarificationAuthorityError(
            f"FORBIDDEN_LIFECYCLE_TRANSITION:{from_state}->{to_state}"
        )


def _assert_registered(repo: Path, authority: Mapping[str, Any]) -> None:
    owner_map = json.loads((repo / OWNER_MAP_REL_PATH).read_text(encoding="utf-8"))
    surfaces = owner_map.get("allowed_optimization_surfaces") or {}
    if AUTHORITY_ID not in surfaces and OWNER_SURFACE not in surfaces:
        raise OperatorClarificationAuthorityError("AUTHORITY_NOT_REGISTERED")
    wiring = json.loads((repo / WIRING_AUTH_REL_PATH).read_text(encoding="utf-8"))
    allowed_paths = set(wiring.get("allowed_paths") or [])
    if AUTHORITY_REL_PATH not in allowed_paths:
        raise OperatorClarificationAuthorityError("AUTHORITY_NOT_REGISTERED")
    classes = set(wiring.get("allowed_surface_classes") or [])
    if (
        "TECHNICAL_BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_OPERATOR_CLARIFICATION_AUTHORITY_V7_WIRING"
        not in classes
    ):
        raise OperatorClarificationAuthorityError("AUTHORITY_NOT_REGISTERED")


def validate_authority(
    authority: Mapping[str, Any],
    *,
    repo_root: Path | None = None,
    require_registered: bool = True,
    require_ready_status: bool = False,
) -> dict[str, Any]:
    repo = repo_root or _repo_root()
    if not authority:
        raise OperatorClarificationAuthorityError("MISSING_AUTHORITY")
    if str(authority.get("authority_id")) != AUTHORITY_ID:
        raise OperatorClarificationAuthorityError("AUTHORITY_ID_MISMATCH")
    if str(authority.get("authority_version")) != AUTHORITY_VERSION:
        raise OperatorClarificationAuthorityError("UNKNOWN_AUTHORITY_VERSION")
    if str(authority.get("schema_version")) != SCHEMA_VERSION:
        raise OperatorClarificationAuthorityError("UNKNOWN_AUTHORITY_VERSION")
    if str(authority.get("hypothesis_id")) != HYPOTHESIS_ID:
        raise OperatorClarificationAuthorityError("HYPOTHESIS_ID_MISMATCH")
    if str(authority.get("preregistration_digest")) != REQUIRED_PREREGISTRATION_DIGEST:
        raise OperatorClarificationAuthorityError("PREREGISTRATION_DIGEST_MISMATCH")
    if authority.get("mutates_preregistration") is not False:
        raise OperatorClarificationAuthorityError("AUTHORITY_CLAIMS_PREREG_MUTATION")
    if authority.get("is_second_preregistration") is not False:
        raise OperatorClarificationAuthorityError("AUTHORITY_CLAIMS_SECOND_PREREG")
    if authority.get("evaluation_authorized") is not False:
        raise OperatorClarificationAuthorityError("AUTHORITY_MUST_KEEP_EVALUATION_UNAUTHORIZED")
    if int(authority.get("evaluation_run_count", -1)) != 0:
        raise OperatorClarificationAuthorityError("AUTHORITY_EVALUATION_RUN_COUNT_NOT_ZERO")
    if str(authority.get("operator_decisions_status")) != OPERATOR_DECISIONS_STATUS:
        raise OperatorClarificationAuthorityError("OPERATOR_DECISIONS_STATUS_MISMATCH")
    if str(authority.get("authority_scope")) != "IMPLEMENTATION_CLARIFICATION_ONLY":
        raise OperatorClarificationAuthorityError("AUTHORITY_SCOPE_MISMATCH")

    computed = compute_authority_digest(authority)
    stored = str(authority.get("authority_digest") or "")
    if not stored or stored != computed:
        raise OperatorClarificationAuthorityError("AUTHORITY_DIGEST_MISMATCH")

    decisions = authority.get("decisions")
    if not isinstance(decisions, Mapping):
        raise OperatorClarificationAuthorityError("UNRESOLVED_B1_THROUGH_B6")
    for key in B1_THROUGH_B6:
        item = decisions.get(key)
        if not isinstance(item, Mapping) or item.get("resolved") is not True:
            raise OperatorClarificationAuthorityError(f"UNRESOLVED_{key}")
    if authority.get("b1_through_b6_fully_resolved") is not True:
        raise OperatorClarificationAuthorityError("UNRESOLVED_B1_THROUGH_B6")

    status = str(authority.get("status") or "")
    if status not in ALLOWED_LIFECYCLE_STATES:
        raise OperatorClarificationAuthorityError("UNKNOWN_LIFECYCLE_STATE")
    if require_ready_status and status != READY_STATUS:
        raise OperatorClarificationAuthorityError(
            f"STATUS_NOT_READY_FOR_OPERATOR_EVALUATION_AUTHORIZATION:{status}"
        )

    if require_registered:
        _assert_registered(repo, authority)

    return {
        "ok": True,
        "authority_id": AUTHORITY_ID,
        "authority_digest": computed,
        "preregistration_digest": REQUIRED_PREREGISTRATION_DIGEST,
        "status": status,
        "operator_decisions_status": OPERATOR_DECISIONS_STATUS,
        "b1_through_b6_fully_resolved": True,
        "evaluation_authorized": False,
        "evaluation_run_count": 0,
    }


def load_and_validate_authority(
    repo_root: Path | None = None,
    *,
    require_registered: bool = True,
    require_ready_status: bool = False,
) -> dict[str, Any]:
    authority = load_authority(repo_root)
    report = validate_authority(
        authority,
        repo_root=repo_root,
        require_registered=require_registered,
        require_ready_status=require_ready_status,
    )
    report["authority"] = authority
    return report


def b7_b8_technical_proof(*, authority: Mapping[str, Any]) -> dict[str, Any]:
    """Authority records that B7/B8 need wiring+tests; does not invent PASS."""
    decisions = authority.get("decisions") or {}
    b7 = decisions.get("B7") or {}
    b8 = decisions.get("B8") or {}
    return {
        "b7_operator": b7.get("pass_operator"),
        "b7_requires_wiring_and_tests": bool(
            b7.get("technically_fulfilled_requires_wiring_and_tests")
        ),
        "b8_requires_wiring_and_tests": bool(
            b8.get("technically_fulfilled_requires_wiring_and_tests")
        ),
        "authority_requires_b7_b8_technical_fulfillment": bool(
            authority.get("b7_b8_technical_fulfillment_required_before_evaluation")
        ),
    }


__all__ = [
    "AUTHORITY_ID",
    "AUTHORITY_REL_PATH",
    "AUTHORITY_VERSION",
    "ALLOWED_LIFECYCLE_STATES",
    "ALLOWED_TRANSITIONS",
    "HYPOTHESIS_ID",
    "OPERATOR_DECISIONS_STATUS",
    "OWNER_SURFACE",
    "PACKAGE_MARKER",
    "READY_STATUS",
    "REQUIRED_PREREGISTRATION_DIGEST",
    "SCHEMA_VERSION",
    "OperatorClarificationAuthorityError",
    "assert_transition_allowed",
    "b7_b8_technical_proof",
    "canonical_json_sha256",
    "compute_authority_digest",
    "load_and_validate_authority",
    "load_authority",
    "validate_authority",
]
