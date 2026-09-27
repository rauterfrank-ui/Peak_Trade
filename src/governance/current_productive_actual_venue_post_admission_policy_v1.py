"""Actual-venue POST admission policy v1 — binds REAL_VENUE_POST_ADMISSION to Owner-GO."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from src.governance.current_productive_real_venue_post_admission_v1 import (
    ADMISSION_OWNER,
    evaluate_real_venue_post_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    POST_OWNER_GO,
)

WORKPACKAGE_ID: Final[str] = (
    "FULL_CORE_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1"
)
BASELINE_ORIGIN_MAIN_SHA: Final[str] = "ef317a10636bada3e2e570a39cc230a035bbfe7b"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/"
    "FULL_CORE_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/current_productive_actual_venue_post_admission_v1_decision.json"
)
OWNER_GO_DECISION_CONFIG: Final[str] = (
    "config/governance/current_productive_actual_venue_post_owner_go_v1_decision.json"
)


@dataclass(frozen=True, slots=True)
class ActualVenuePostAdmissionPolicyResultV1:
    policy_valid: bool
    post_owner_go_token: str
    admission_owner: str
    baseline_origin_main_sha: str


def validate_actual_venue_post_admission_policy_v1(
    *, repo_root: Path | None = None
) -> ActualVenuePostAdmissionPolicyResultV1:
    root = repo_root or Path(__file__).resolve().parents[2]
    decision_path = root / DECISION_CONFIG
    owner_path = root / OWNER_GO_DECISION_CONFIG
    spec_path = root / NORMATIVE_SPEC
    if not decision_path.is_file() or not owner_path.is_file() or not spec_path.is_file():
        return ActualVenuePostAdmissionPolicyResultV1(
            policy_valid=False,
            post_owner_go_token=POST_OWNER_GO,
            admission_owner=ADMISSION_OWNER,
            baseline_origin_main_sha=BASELINE_ORIGIN_MAIN_SHA,
        )
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    owner = json.loads(owner_path.read_text(encoding="utf-8"))
    ok = (
        decision.get("workpackage_id") == WORKPACKAGE_ID
        and owner.get("owner_go_token") == POST_OWNER_GO
        and owner.get("baseline_origin_main_sha") == BASELINE_ORIGIN_MAIN_SHA
        and decision.get("post_allowed") is False
        and decision.get("real_venue_post_allowed") is False
    )
    return ActualVenuePostAdmissionPolicyResultV1(
        policy_valid=ok is True,
        post_owner_go_token=POST_OWNER_GO,
        admission_owner=ADMISSION_OWNER,
        baseline_origin_main_sha=BASELINE_ORIGIN_MAIN_SHA,
    )


def prove_actual_venue_post_admission_requires_durable_owner_go_v1(
    *, repo_root: Path, store_root: Path
) -> bool:
    admission = evaluate_real_venue_post_admission_v1(
        post_owner_go=POST_OWNER_GO,
        one_shot_real_post=True,
        permit=None,
        store_root=store_root,
    )
    return admission.post_admission_granted is not True


__all__ = [
    "BASELINE_ORIGIN_MAIN_SHA",
    "DECISION_CONFIG",
    "OWNER_GO_DECISION_CONFIG",
    "WORKPACKAGE_ID",
    "ActualVenuePostAdmissionPolicyResultV1",
    "prove_actual_venue_post_admission_requires_durable_owner_go_v1",
    "validate_actual_venue_post_admission_policy_v1",
]
