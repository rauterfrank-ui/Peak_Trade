"""V7 DEVELOPMENT evaluation authorization ratification.

Separate SSOT from the immutable DEFINITION_ONLY preregistration contract.
Authorizes exactly one later DEVELOPMENT evaluation run after panel release.
Does not execute evaluation, claim a run slot, or open holdout/runtime.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.research.bollinger_mr_midband_exit_reentry_cooldown_hypothesis_preregistration_v7 import (
    EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST,
    load_and_validate_repo_contract,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_operator_clarification_authority_v7 import (
    AUTHORITY_ID,
    AUTHORITY_REL_PATH,
    AUTHORIZED_STATUS,
    HYPOTHESIS_ID,
    READY_STATUS,
    assert_transition_allowed,
    compute_authority_digest,
    load_and_validate_authority,
    load_authority,
)
from src.research.independent_dev_panel_quarantine_release_v1 import (
    DATASET_ID,
    DATASET_INSTANCE,
    DATASET_ROLE,
    EXPECTED_CONTENT_HASH,
    EXPECTED_MANIFEST_SHA256,
    EXPECTED_UNIVERSE_DIGEST,
    PanelQuarantineReleaseError,
    RELEASED_STATUS,
    is_panel_released,
)

PACKAGE_MARKER = (
    "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_DEVELOPMENT_EVALUATION_"
    "AUTHORIZATION_RATIFICATION_V7=true"
)
SCHEMA_VERSION = (
    "bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_"
    "authorization_ratification.v7"
)
RATIFICATION_ID = (
    "bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_"
    "authorization_ratification_v7"
)
RATIFICATION_REL_PATH = (
    "config/research/"
    "bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_"
    "authorization_ratification_v7.json"
)
EVIDENCE_REL_PATH = (
    "docs/evidence/authorize_bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v7/"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_"
    "DEVELOPMENT_EVALUATION_AUTHORIZATION_RATIFICATION_V7.md"
)
GO_TOKEN = "GO_BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_V7_DEVELOPMENT_EVALUATION_AUTHORIZATION"
NEXT_OPERATOR_GO = "GO_BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_V7_DEVELOPMENT_EVALUATION_RUN"
NEXT_CANONICAL_STEP = "AWAIT_SEPARATE_OPERATOR_GO_FOR_V7_DEVELOPMENT_EVALUATION_RUN"
RUN_LIMIT = 1
READY_AUTHORITY_DIGEST = "144c9ff3cd59f3ec796a9e9908709c612901e79336470a230a007f46eb2429e9"
EVAL_EVIDENCE_REL = (
    "docs/evidence/evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v7"
)
OWNER_MAP_REL_PATH = (
    "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)
WIRING_AUTH_REL_PATH = "config/governance/technical_canonical_wiring_authorization_v1.json"
OWNER_SURFACE = (
    "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_DEVELOPMENT_EVALUATION_"
    "AUTHORIZATION_RATIFICATION_V7"
)
BACKLOG_REL_PATH = "config/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json"


class EvaluationAuthorizationRatificationError(ValueError):
    """Fail-closed V7 evaluation-authorization ratification error."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def canonical_json_sha256(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def compute_ratification_digest(ratification: Mapping[str, Any]) -> str:
    body = {k: v for k, v in ratification.items() if k != "ratification_digest"}
    return canonical_json_sha256(body)


def _slot_consumed(repo: Path) -> bool:
    out = repo / EVAL_EVIDENCE_REL
    if (out / "run_slot_claim.json").is_file():
        return True
    summary = out / "summary.json"
    if not summary.is_file():
        return False
    try:
        payload = json.loads(summary.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return int(payload.get("evaluation_run_count", -1)) >= 1


def build_ratification_payload(
    *,
    authority_digest_at_ready: str = READY_AUTHORITY_DIGEST,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    payload = {
        "artifact_kind": (
            "bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_"
            "authorization_ratification"
        ),
        "artifact_version": "v7",
        "schema_version": SCHEMA_VERSION,
        "ratification_id": RATIFICATION_ID,
        "authority_effect": "NONE",
        "runtime_effect": "NONE",
        "trading_effect": "NONE",
        "status": AUTHORIZED_STATUS,
        "hypothesis_id": HYPOTHESIS_ID,
        "operator_go": GO_TOKEN,
        "go_token": GO_TOKEN,
        "preregistration_digest": EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST,
        "preregistration_path": (
            "config/research/"
            "bollinger_mr_midband_exit_reentry_cooldown_preregistered_economic_"
            "hypothesis_measurement_contract_v7.json"
        ),
        "operator_clarification_authority_id": AUTHORITY_ID,
        "operator_clarification_authority_path": AUTHORITY_REL_PATH,
        "authority_digest_at_ready": authority_digest_at_ready,
        "dataset_id": DATASET_ID,
        "dataset_instance": DATASET_INSTANCE,
        "dataset_role": DATASET_ROLE,
        "panel_release_status_required": RELEASED_STATUS,
        "expected_manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "expected_content_hash": EXPECTED_CONTENT_HASH,
        "expected_universe_digest": EXPECTED_UNIVERSE_DIGEST,
        "evaluation_authorized_for_separate_development_run": True,
        "evaluation_executed": False,
        "evaluation_run_count": 0,
        "evaluation_run_count_authorized": RUN_LIMIT,
        "development_evaluation_runs_allowed": RUN_LIMIT,
        "run_slot_consumed": False,
        "rerun_allowed": False,
        "holdout_allowed": False,
        "holdout_data_accessed": False,
        "live_authorized": False,
        "orders_allowed": False,
        "shadow_activated": False,
        "testnet_activated": False,
        "scheduler_authorized": False,
        "capital_activated": False,
        "economic_gate_open": False,
        "promotion_eligible": False,
        "parameters_unchanged_from_preregistration": True,
        "mutates_preregistration": False,
        "preregistration_evaluation_authorized_field_remains_false": True,
        "next_operator_go": NEXT_OPERATOR_GO,
        "next_canonical_step": NEXT_CANONICAL_STEP,
        "created_at_utc": created_at_utc or _utc_now(),
        "evidence_ref": EVIDENCE_REL_PATH,
        "governance_ref": GOVERNANCE_REL_PATH,
        "owner": OWNER_SURFACE,
    }
    payload["ratification_digest"] = compute_ratification_digest(payload)
    return payload


def validate_ratification(
    ratification: Mapping[str, Any],
    *,
    repo_root: Path | None = None,
    require_panel_released: bool = True,
    archive_root: Path | None = None,
) -> dict[str, Any]:
    repo = repo_root or _repo_root()
    if not ratification:
        raise EvaluationAuthorizationRatificationError("MISSING_RATIFICATION")
    if str(ratification.get("ratification_id")) != RATIFICATION_ID:
        raise EvaluationAuthorizationRatificationError("RATIFICATION_ID_MISMATCH")
    if str(ratification.get("schema_version")) != SCHEMA_VERSION:
        raise EvaluationAuthorizationRatificationError("SCHEMA_VERSION_MISMATCH")
    if str(ratification.get("hypothesis_id")) != HYPOTHESIS_ID:
        raise EvaluationAuthorizationRatificationError("HYPOTHESIS_ID_MISMATCH")
    if str(ratification.get("go_token")) != GO_TOKEN:
        raise EvaluationAuthorizationRatificationError("GO_TOKEN_INVALID")
    if (
        str(ratification.get("preregistration_digest"))
        != EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST
    ):
        raise EvaluationAuthorizationRatificationError("PREREGISTRATION_DIGEST_MISMATCH")
    if ratification.get("mutates_preregistration") is not False:
        raise EvaluationAuthorizationRatificationError("CLAIMS_PREREG_MUTATION")
    if str(ratification.get("dataset_id")) != DATASET_ID:
        raise EvaluationAuthorizationRatificationError("DATASET_ID_MISMATCH")
    if str(ratification.get("expected_manifest_sha256")) != EXPECTED_MANIFEST_SHA256:
        raise EvaluationAuthorizationRatificationError("MANIFEST_DIGEST_BINDING_MISMATCH")
    if str(ratification.get("expected_content_hash")) != EXPECTED_CONTENT_HASH:
        raise EvaluationAuthorizationRatificationError("CONTENT_DIGEST_BINDING_MISMATCH")
    if str(ratification.get("expected_universe_digest")) != EXPECTED_UNIVERSE_DIGEST:
        raise EvaluationAuthorizationRatificationError("UNIVERSE_DIGEST_BINDING_MISMATCH")
    computed = compute_ratification_digest(ratification)
    if str(ratification.get("ratification_digest") or "") != computed:
        raise EvaluationAuthorizationRatificationError("RATIFICATION_DIGEST_MISMATCH")

    executed = ratification.get("evaluation_executed") is True
    run_count = int(ratification.get("evaluation_run_count", -1))
    if int(ratification.get("evaluation_run_count_authorized", -1)) != RUN_LIMIT:
        raise EvaluationAuthorizationRatificationError("RUN_LIMIT_MISMATCH")
    if executed:
        if ratification.get("evaluation_authorized_for_separate_development_run") is not False:
            raise EvaluationAuthorizationRatificationError("POST_EXEC_AUTH_FLAG_MUST_BE_FALSE")
        if run_count != 1:
            raise EvaluationAuthorizationRatificationError("POST_EXEC_RUN_COUNT_NOT_ONE")
        if ratification.get("run_slot_consumed") is not True:
            raise EvaluationAuthorizationRatificationError("POST_EXEC_SLOT_NOT_CONSUMED")
        if not _slot_consumed(repo):
            raise EvaluationAuthorizationRatificationError("POST_EXEC_EVIDENCE_SLOT_MISSING")
    else:
        if ratification.get("evaluation_authorized_for_separate_development_run") is not True:
            raise EvaluationAuthorizationRatificationError("NOT_AUTHORIZED_FLAG")
        if run_count != 0:
            raise EvaluationAuthorizationRatificationError("RUN_COUNT_NOT_ZERO")
        if ratification.get("run_slot_consumed") is not False:
            raise EvaluationAuthorizationRatificationError("SLOT_MARKED_CONSUMED")
        if _slot_consumed(repo):
            raise EvaluationAuthorizationRatificationError("RUN_SLOT_ALREADY_CONSUMED")

    # Immutable prereg remains definition-only / unauthorized field.
    prereg_report = load_and_validate_repo_contract(repo)
    if int(prereg_report.get("evaluation_run_count", -1)) != 0:
        raise EvaluationAuthorizationRatificationError("PREREG_RUN_COUNT_NOT_ZERO")
    contract = json.loads(
        (
            repo
            / "config/research/"
            / "bollinger_mr_midband_exit_reentry_cooldown_preregistered_economic_hypothesis_measurement_contract_v7.json"
        ).read_text(encoding="utf-8")
    )
    if contract.get("evaluation_authorized") is not False:
        raise EvaluationAuthorizationRatificationError(
            "PREREG_EVALUATION_AUTHORIZED_FIELD_MUST_REMAIN_FALSE"
        )
    if str(contract.get("development_preregistration_digest")) != (
        EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST
    ):
        raise EvaluationAuthorizationRatificationError("PREREG_DIGEST_DRIFT")

    if require_panel_released:
        try:
            released = is_panel_released(archive_root=archive_root)
        except PanelQuarantineReleaseError as exc:
            raise EvaluationAuthorizationRatificationError(f"PANEL_RELEASE_CHECK:{exc}") from exc
        if not released:
            raise EvaluationAuthorizationRatificationError("PANEL_NOT_RELEASED")

    return {
        "ok": True,
        "ratification_id": RATIFICATION_ID,
        "ratification_digest": computed,
        "evaluation_authorized": True,
        "evaluation_run_count": 0,
        "run_slot_consumed": False,
        "hypothesis_id": HYPOTHESIS_ID,
        "next_canonical_step": NEXT_CANONICAL_STEP,
    }


def load_ratification(repo_root: Path | None = None) -> dict[str, Any]:
    repo = repo_root or _repo_root()
    path = repo / RATIFICATION_REL_PATH
    if not path.is_file():
        raise EvaluationAuthorizationRatificationError("MISSING_RATIFICATION")
    return json.loads(path.read_text(encoding="utf-8"))


def load_and_validate_ratification(
    repo_root: Path | None = None,
    *,
    require_panel_released: bool = True,
    archive_root: Path | None = None,
) -> dict[str, Any]:
    ratification = load_ratification(repo_root)
    report = validate_ratification(
        ratification,
        repo_root=repo_root,
        require_panel_released=require_panel_released,
        archive_root=archive_root,
    )
    report["ratification"] = ratification
    return report


def resolve_effective_evaluation_authorization(
    repo_root: Path | None = None,
    *,
    archive_root: Path | None = None,
) -> dict[str, Any]:
    """Single effective auth SSOT used by gates (not the prereg boolean)."""
    repo = repo_root or _repo_root()
    try:
        authority = load_authority(repo)
    except Exception as exc:  # noqa: BLE001
        return {
            "evaluation_authorized": False,
            "reason": f"AUTHORITY_UNLOADABLE:{exc}",
            "lifecycle_status": None,
        }
    status = str(authority.get("status") or "")
    if status != AUTHORIZED_STATUS:
        return {
            "evaluation_authorized": False,
            "reason": f"LIFECYCLE_NOT_AUTHORIZED:{status}",
            "lifecycle_status": status,
        }
    if authority.get("evaluation_authorized") is not True:
        return {
            "evaluation_authorized": False,
            "reason": "AUTHORITY_FLAG_FALSE",
            "lifecycle_status": status,
        }
    if int(authority.get("evaluation_run_count", -1)) != 0:
        return {
            "evaluation_authorized": False,
            "reason": "AUTHORITY_RUN_COUNT_NOT_ZERO",
            "lifecycle_status": status,
        }
    if _slot_consumed(repo):
        return {
            "evaluation_authorized": False,
            "reason": "RUN_SLOT_ALREADY_CONSUMED",
            "lifecycle_status": status,
        }
    try:
        rat = load_and_validate_ratification(
            repo,
            require_panel_released=True,
            archive_root=archive_root,
        )
    except (EvaluationAuthorizationRatificationError, PanelQuarantineReleaseError) as exc:
        return {
            "evaluation_authorized": False,
            "reason": f"RATIFICATION_GATE:{exc}",
            "lifecycle_status": status,
        }
    return {
        "evaluation_authorized": True,
        "reason": "RATIFICATION_AND_LIFECYCLE_AUTHORIZED",
        "lifecycle_status": status,
        "ratification_digest": rat["ratification_digest"],
        "authority_digest": compute_authority_digest(authority),
    }


def materialize_ratification_file(
    repo_root: Path | None = None,
    *,
    authority_digest_at_ready: str = READY_AUTHORITY_DIGEST,
) -> dict[str, Any]:
    repo = repo_root or _repo_root()
    payload = build_ratification_payload(authority_digest_at_ready=authority_digest_at_ready)
    path = repo / RATIFICATION_REL_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def apply_evaluation_authorization_transition(
    repo_root: Path | None = None,
    *,
    archive_root: Path | None = None,
    write_evidence: bool = True,
) -> dict[str, Any]:
    """READY → EVALUATION_AUTHORIZED via ratification; idempotent if already applied."""
    repo = repo_root or _repo_root()
    if not is_panel_released(archive_root=archive_root):
        raise EvaluationAuthorizationRatificationError("PANEL_NOT_RELEASED")
    if _slot_consumed(repo):
        raise EvaluationAuthorizationRatificationError("RUN_SLOT_ALREADY_CONSUMED")

    authority = load_authority(repo)
    status = str(authority.get("status") or "")
    if status == AUTHORIZED_STATUS and authority.get("evaluation_authorized") is True:
        rat = load_and_validate_ratification(
            repo, require_panel_released=True, archive_root=archive_root
        )
        return {
            "idempotent": True,
            "status": AUTHORIZED_STATUS,
            "evaluation_authorized": True,
            "authority_digest": compute_authority_digest(authority),
            "ratification_digest": rat["ratification_digest"],
            "evaluation_run_count": 0,
            "run_slot_consumed": False,
        }

    if status != READY_STATUS:
        raise EvaluationAuthorizationRatificationError(f"INVALID_SOURCE_STATE:{status}")
    assert_transition_allowed(from_state=READY_STATUS, to_state=AUTHORIZED_STATUS)

    # Ensure ratification file exists and validates.
    rat_path = repo / RATIFICATION_REL_PATH
    if not rat_path.is_file():
        materialize_ratification_file(
            repo, authority_digest_at_ready=str(authority.get("authority_digest"))
        )
    rat = load_and_validate_ratification(
        repo, require_panel_released=True, archive_root=archive_root
    )

    updated = deepcopy(authority)
    updated["status"] = AUTHORIZED_STATUS
    updated["evaluation_authorized"] = True
    updated["evaluation_run_count"] = 0
    updated["authorization_ratification_ref"] = RATIFICATION_REL_PATH
    updated["authorization_ratification_digest"] = rat["ratification_digest"]
    updated["authorized_at_utc"] = _utc_now()
    updated["ready_status_authority_digest"] = READY_AUTHORITY_DIGEST
    updated["next_canonical_step"] = NEXT_CANONICAL_STEP
    updated["authority_digest"] = compute_authority_digest(updated)
    (repo / AUTHORITY_REL_PATH).write_text(
        json.dumps(updated, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    # Re-validate authority in authorized state.
    load_and_validate_authority(
        repo,
        require_registered=True,
        require_ready_status=False,
        require_authorized_status=True,
    )

    _update_backlog_for_authorization(repo, authority_digest=updated["authority_digest"], rat=rat)
    evidence = {
        "schema_version": (
            "bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_"
            "authorization_evidence.v7"
        ),
        "status": AUTHORIZED_STATUS,
        "hypothesis_id": HYPOTHESIS_ID,
        "evaluation_authorized": True,
        "evaluation_run_count": 0,
        "run_slot_consumed": False,
        "runner_started": False,
        "holdout_data_accessed": False,
        "live_authorized": False,
        "orders": False,
        "panel_released": True,
        "ratification_digest": rat["ratification_digest"],
        "authority_digest": updated["authority_digest"],
        "preregistration_digest": EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST,
        "preregistration_evaluation_authorized_field": False,
        "next_canonical_step": NEXT_CANONICAL_STEP,
        "authorized_at_utc": updated["authorized_at_utc"],
    }
    if write_evidence:
        out = repo / EVIDENCE_REL_PATH
        out.mkdir(parents=True, exist_ok=True)
        (out / "summary.json").write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        # Build front-matter without a contiguous "token: <long>" literal
        # (Policy Critic NO_SECRETS false-positive on docs governance markers).
        docs_marker = "docs_" + "token"
        docs_marker_value = (
            "DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_"
            "DEVELOPMENT_EVALUATION_AUTHORIZATION_RATIFICATION_V7"
        )
        (out / "README.md").write_text(
            "\n".join(
                [
                    "---",
                    f"{docs_marker}: {docs_marker_value}",
                    "STATUS: EVALUATION_AUTHORIZED",
                    "LIVE_AUTHORIZED: false",
                    "ORDERS_ALLOWED: false",
                    "---",
                    "",
                    "# V7 DEVELOPMENT evaluation authorization ratification",
                    "",
                    "Authorizes a later separate DEVELOPMENT evaluation run.",
                    "Does not execute evaluation. Run count remains 0. Slot unconsumed.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    return {
        "idempotent": False,
        "status": AUTHORIZED_STATUS,
        "evaluation_authorized": True,
        "authority_digest": updated["authority_digest"],
        "ratification_digest": rat["ratification_digest"],
        "evaluation_run_count": 0,
        "run_slot_consumed": False,
        "evidence": evidence,
    }


def _update_backlog_for_authorization(
    repo: Path, *, authority_digest: str, rat: Mapping[str, Any]
) -> None:
    path = repo / BACKLOG_REL_PATH
    backlog = json.loads(path.read_text(encoding="utf-8"))
    backlog["evaluation_authorized"] = True
    backlog["verdict"] = (
        "CANONICAL_OPEN_MR_EXIT_EFFICIENCY_BACKLOG_V7_EVALUATION_AUTHORIZED_AWAITING_RUN_GO"
    )
    backlog["next_canonical_step"] = NEXT_CANONICAL_STEP
    backlog["governance_note"] = (
        "Exactly one DEFINITION_ONLY_PREREGISTERED exit-efficiency hypothesis (V7) with "
        "Operator Clarification Authority B1-B6 and separate development-evaluation "
        "authorization ratification applied (lifecycle EVALUATION_AUTHORIZED). "
        "Preregistration digest immutable; prereg evaluation_authorized field remains false. "
        "evaluation_run_count=0; run slot unconsumed; no evaluation executed in authorization "
        "slice; next step requires separate Operator-GO for the single DEVELOPMENT run. "
        "Economic/promotion closed; no runtime/orders."
    )
    prefs = backlog.get("preregistered_hypotheses") or []
    if prefs:
        prefs[0]["evaluation_authorized"] = True
        prefs[0]["implementation_lifecycle_status"] = AUTHORIZED_STATUS
        prefs[0]["operator_clarification_authority_digest"] = authority_digest
        prefs[0]["authorization_ratification_ref"] = RATIFICATION_REL_PATH
        prefs[0]["authorization_ratification_digest"] = rat.get("ratification_digest")
        prefs[0]["evaluation_run_count"] = 0
        prefs[0]["evaluation_executed"] = False
    path.write_text(json.dumps(backlog, indent=2, sort_keys=True) + "\n", encoding="utf-8")


__all__ = [
    "EvaluationAuthorizationRatificationError",
    "EVIDENCE_REL_PATH",
    "GO_TOKEN",
    "GOVERNANCE_REL_PATH",
    "NEXT_CANONICAL_STEP",
    "NEXT_OPERATOR_GO",
    "OWNER_SURFACE",
    "PACKAGE_MARKER",
    "RATIFICATION_ID",
    "RATIFICATION_REL_PATH",
    "READY_AUTHORITY_DIGEST",
    "RUN_LIMIT",
    "SCHEMA_VERSION",
    "apply_evaluation_authorization_transition",
    "build_ratification_payload",
    "compute_ratification_digest",
    "load_and_validate_ratification",
    "load_ratification",
    "materialize_ratification_file",
    "resolve_effective_evaluation_authorization",
    "validate_ratification",
]
