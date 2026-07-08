"""Full canonical core completion and plausibility evaluation v0.

Owner-ratified diagnostic evidence class for full-chain system completion and
plausibility evaluation. Diagnostic-only: no runtime, orders, promotion, or
economic validity claims.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    HISTORICAL_STEP31F_BINDING_COMPLETION_DIGEST,
    ORDER_EFFECT,
    REASON_NEW_EVIDENCE_CLASS_REQUIRED,
    REASON_UNMODIFIED_BINDING_RETRY_BLOCKED,
    REASON_WORKTREE_NOT_CLEAN,
    RUNTIME_EFFECT,
)

PACKAGE_MARKER = "FULL_CANONICAL_CORE_COMPLETION_AND_PLAUSIBILITY_EVALUATION_V0=true"

SCHEMA_VERSION = "full_canonical_core_completion_plausibility_evaluation.v0"
EVIDENCE_CLASS_ID = "FULL_CANONICAL_CORE_COMPLETION_AND_PLAUSIBILITY_EVALUATION_V0"
PURPOSE = "CORE_SYSTEM_COMPLETION_DIAGNOSTIC"
DIAGNOSTIC_STATUS = "SYSTEM_DIAGNOSTIC_ONLY"

OWNER_POLICY_REL = (
    "config/research/full_canonical_core_completion_plausibility_evaluation_policy_v0.json"
)
CONFIRM_GO = "GO_FULL_CANONICAL_CORE_COMPLETION_AND_PLAUSIBILITY_EVALUATION_DIAGNOSTIC_V0"

DIAGNOSTIC_TOLERATED_UNTRACKED_PATHS: frozenset[str] = frozenset(
    {".python-version", ".comparison_ssot_pytest_outputs/"}
)

REASON_OWNER_POLICY_MISSING = "OWNER_POLICY_CONFIG_MISSING"
REASON_OWNER_POLICY_DIGEST_MISMATCH = "OWNER_POLICY_DECISION_DIGEST_MISMATCH"
REASON_OWNER_POLICY_EVIDENCE_CLASS_MISMATCH = "OWNER_POLICY_EVIDENCE_CLASS_MISMATCH"
REASON_OWNER_POLICY_PURPOSE_MISMATCH = "OWNER_POLICY_PURPOSE_MISMATCH"
REASON_OWNER_POLICY_AUTHORITY_FLAG_TRUE = "OWNER_POLICY_AUTHORITY_FLAG_TRUE"
REASON_OWNER_POLICY_GLOBAL_OVERRIDE_TRUE = "OWNER_POLICY_GLOBAL_OVERRIDE_TRUE"
REASON_OWNER_POLICY_HISTORICAL_RECLASSIFICATION_ALLOWED = (
    "OWNER_POLICY_HISTORICAL_RECLASSIFICATION_ALLOWED"
)
REASON_OWNER_POLICY_NOT_DIAGNOSTIC = "OWNER_POLICY_NOT_SYSTEM_DIAGNOSTIC_ONLY"
REASON_HISTORICAL_NEGATIVE_EVIDENCE_MUTATION = "HISTORICAL_NEGATIVE_EVIDENCE_MUTATION_BLOCKED"
REASON_UNTOLERATED_UNTRACKED_PATH = "UNTOLERATED_UNTRACKED_PATH"

_AUTHORITY_FLAG_FIELDS: tuple[str, ...] = (
    "live_authorized",
    "orders_allowed",
    "scheduler_runtime_allowed",
    "shadow_authorized",
    "paper_authorized",
    "testnet_authorized",
    "canary_authorized",
    "adapter_submission_allowed",
    "credential_access_allowed",
    "runtime_rewire_allowed",
    "promotion_admissible",
    "runtime_admissible",
    "economic_validity_claim_allowed",
)

DEFAULT_DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
DURABLE_EVIDENCE_SUBDIR = "research"
DURABLE_EVIDENCE_BUNDLE_PREFIX = "full_canonical_core_completion_plausibility_evaluation_v0"

PROMOTION_BOUNDARY_STATUS = "DIAGNOSTIC_ONLY_NOT_PROMOTION_EVIDENCE"
PROMOTION_BOUNDARY_REASON_CODES: tuple[str, ...] = (
    "FULL_CANONICAL_CHAIN_PARITY_REQUIRED_BEFORE_SYSTEM_ECONOMIC_EVIDENCE",
    "ECONOMIC_VIABILITY_EVIDENCE_V1_PASS_REQUIRED_BEFORE_PROMOTION_ADMISSIBILITY",
    "DIAGNOSTIC_RESULT_IS_NOT_PROMOTION_EVIDENCE",
    "RAW_RESEARCH_EVIDENCE_IS_NOT_SYSTEM_ECONOMIC_EVIDENCE",
)


@dataclass(frozen=True)
class StartStateVerificationResultV0:
    valid: bool
    fail_reasons: tuple[str, ...]
    origin_main_sha: str
    owner_policy: dict[str, Any]
    fleet_binding_completion: dict[str, Any]
    tolerated_untracked_paths: tuple[str, ...]


@dataclass(frozen=True)
class DiagnosticExecutionResultV0:
    status: str
    promotion_admissible: bool
    runtime_admissible: bool
    live_authorized: bool
    orders_allowed: bool
    economic_validity_claim_allowed: bool
    system_economic_evidence_admissible: bool
    scheduler_runtime_allowed: bool
    shadow_authorized: bool
    paper_authorized: bool
    testnet_authorized: bool
    canary_authorized: bool
    credential_access_allowed: bool
    promotion_boundary_status: str
    promotion_boundary_reason_codes: tuple[str, ...]
    owner_policy_decision_digest: str
    evidence_class_id: str
    parity_status_counts: dict[str, int]
    evidence_root: Path
    manifest_verify_rc: int


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_owner_policy_decision_digest_v0(policy: Mapping[str, Any]) -> str:
    body = {key: value for key, value in policy.items() if key != "owner_policy_decision_digest"}
    return _stable_digest(body)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"not_object:{path}")
    return payload


def _resolve_origin_main_sha(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "origin/main"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _git_status_porcelain(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def _path_from_porcelain_line(line: str) -> str:
    return line[3:].strip()


def _is_tolerated_untracked_path(path: str) -> bool:
    if path in DIAGNOSTIC_TOLERATED_UNTRACKED_PATHS:
        return True
    return any(
        path == tolerated or path.startswith(tolerated)
        for tolerated in DIAGNOSTIC_TOLERATED_UNTRACKED_PATHS
    )


def list_non_tolerated_untracked_paths_v0(repo_root: Path) -> tuple[str, ...]:
    blocked: list[str] = []
    for line in _git_status_porcelain(repo_root):
        status = line[:2]
        path = _path_from_porcelain_line(line)
        if status.strip() == "??" and not _is_tolerated_untracked_path(path):
            blocked.append(path)
        elif status.strip() != "??" and not _is_tolerated_untracked_path(path):
            blocked.append(path)
    return tuple(blocked)


def list_tolerated_untracked_paths_v0(repo_root: Path) -> tuple[str, ...]:
    tolerated: list[str] = []
    for line in _git_status_porcelain(repo_root):
        status = line[:2]
        if status.strip() != "??":
            continue
        path = _path_from_porcelain_line(line)
        if _is_tolerated_untracked_path(path):
            tolerated.append(path)
    return tuple(tolerated)


def is_worktree_clean_for_diagnostic_evidence_class_v0(
    repo_root: Path,
) -> tuple[bool, tuple[str, ...]]:
    blocked = list_non_tolerated_untracked_paths_v0(repo_root)
    if blocked:
        return False, tuple(f"{REASON_UNTOLERATED_UNTRACKED_PATH}:{path}" for path in blocked)
    return True, ()


def verify_owner_policy_for_unmodified_retry_exception_v0(
    owner_policy: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    return verify_owner_policy_v0(owner_policy)


def verify_owner_policy_v0(owner_policy: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if str(owner_policy.get("evidence_class", "")) != EVIDENCE_CLASS_ID:
        reasons.append(REASON_OWNER_POLICY_EVIDENCE_CLASS_MISMATCH)
    if str(owner_policy.get("evidence_class_id", "")) != EVIDENCE_CLASS_ID:
        reasons.append(REASON_OWNER_POLICY_EVIDENCE_CLASS_MISMATCH)
    if str(owner_policy.get("purpose", "")) != PURPOSE:
        reasons.append(REASON_OWNER_POLICY_PURPOSE_MISMATCH)
    expected_digest = compute_owner_policy_decision_digest_v0(owner_policy)
    actual_digest = str(owner_policy.get("owner_policy_decision_digest", ""))
    if actual_digest != expected_digest:
        reasons.append(REASON_OWNER_POLICY_DIGEST_MISMATCH)
    if owner_policy.get("unmodified_binding_retry_global_override") is not False:
        reasons.append(REASON_OWNER_POLICY_GLOBAL_OVERRIDE_TRUE)
    if owner_policy.get("historical_negative_evidence_reclassification_allowed") is not False:
        reasons.append(REASON_OWNER_POLICY_HISTORICAL_RECLASSIFICATION_ALLOWED)
    if owner_policy.get("system_diagnostic_only") is not True:
        reasons.append(REASON_OWNER_POLICY_NOT_DIAGNOSTIC)
    for field in _AUTHORITY_FLAG_FIELDS:
        if owner_policy.get(field) is not False:
            reasons.append(f"{REASON_OWNER_POLICY_AUTHORITY_FLAG_TRUE}:{field}")
    return not reasons, tuple(reasons)


def verify_historical_negative_evidence_immutable_v0(
    *,
    fleet_binding_completion: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    completion_digest = str(fleet_binding_completion.get("completion_digest", ""))
    if completion_digest != HISTORICAL_STEP31F_BINDING_COMPLETION_DIGEST:
        return True, ()
    if fleet_binding_completion.get("economic_validity_offline_gate_pass") is not False:
        return False, (REASON_HISTORICAL_NEGATIVE_EVIDENCE_MUTATION,)
    return True, ()


def verify_unmodified_retry_for_diagnostic_evidence_class_v0(
    *,
    fleet_binding_completion: Mapping[str, Any],
    owner_policy: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    policy_ok, policy_reasons = verify_owner_policy_v0(owner_policy)
    if not policy_ok:
        return False, policy_reasons
    completion_digest = str(fleet_binding_completion.get("completion_digest", ""))
    if completion_digest != HISTORICAL_STEP31F_BINDING_COMPLETION_DIGEST:
        return True, ()
    immutable_ok, immutable_reasons = verify_historical_negative_evidence_immutable_v0(
        fleet_binding_completion=fleet_binding_completion,
    )
    if not immutable_ok:
        return False, immutable_reasons
    return True, ()


def verify_execution_start_state_v0(
    *,
    repo_root: Path,
    fleet_binding_completion: Mapping[str, Any] | None = None,
    owner_policy: Mapping[str, Any] | None = None,
) -> StartStateVerificationResultV0:
    reasons: list[str] = []
    origin_main = _resolve_origin_main_sha(repo_root)
    if not origin_main:
        reasons.append("ORIGIN_MAIN_RESOLVE_FAILED")

    policy_path = repo_root / OWNER_POLICY_REL
    if owner_policy is None:
        if not policy_path.is_file():
            reasons.append(REASON_OWNER_POLICY_MISSING)
            owner_policy = {}
        else:
            owner_policy = _load_json(policy_path)

    if fleet_binding_completion is None:
        binding_path = (
            repo_root / "config/research/final_research_fleet_versioned_binding_completion_v0.json"
        )
        if not binding_path.is_file():
            reasons.append("BINDING_COMPLETION_MISSING")
            fleet_binding_completion = {}
        else:
            fleet_binding_completion = _load_json(binding_path)

    if owner_policy:
        policy_ok, policy_reasons = verify_owner_policy_v0(owner_policy)
        if not policy_ok:
            reasons.extend(policy_reasons)

    if fleet_binding_completion and owner_policy:
        retry_ok, retry_reasons = verify_unmodified_retry_for_diagnostic_evidence_class_v0(
            fleet_binding_completion=fleet_binding_completion,
            owner_policy=owner_policy,
        )
        if not retry_ok:
            reasons.extend(retry_reasons)

    worktree_ok, worktree_reasons = is_worktree_clean_for_diagnostic_evidence_class_v0(repo_root)
    if not worktree_ok:
        reasons.extend(worktree_reasons)

    tolerated = list_tolerated_untracked_paths_v0(repo_root)

    return StartStateVerificationResultV0(
        valid=not reasons,
        fail_reasons=tuple(reasons),
        origin_main_sha=origin_main,
        owner_policy=dict(owner_policy or {}),
        fleet_binding_completion=dict(fleet_binding_completion or {}),
        tolerated_untracked_paths=tolerated,
    )


def build_diagnostic_output_v0(
    *,
    owner_policy: Mapping[str, Any],
    parity_status_counts: Mapping[str, int],
) -> dict[str, Any]:
    return {
        "status": DIAGNOSTIC_STATUS,
        "promotion_admissible": False,
        "runtime_admissible": False,
        "live_authorized": False,
        "orders_allowed": False,
        "economic_validity_claim_allowed": False,
        "system_economic_evidence_admissible": False,
        "promotion_boundary_status": PROMOTION_BOUNDARY_STATUS,
        "promotion_boundary_reason_codes": list(PROMOTION_BOUNDARY_REASON_CODES),
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "purpose": PURPOSE,
        "owner_policy_decision_digest": str(owner_policy.get("owner_policy_decision_digest", "")),
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "parity_status_counts": dict(parity_status_counts),
        "tolerated_untracked_artefacts": sorted(DIAGNOSTIC_TOLERATED_UNTRACKED_PATHS),
    }


def run_diagnostic_evaluation_v0(
    *,
    confirm: str,
    repo_root: Path,
    durable_evidence_root: Path = DEFAULT_DURABLE_ARCHIVE_ROOT,
) -> DiagnosticExecutionResultV0:
    if confirm != CONFIRM_GO:
        raise ValueError(f"CONFIRM_GO_INVALID:{confirm}")

    start_state = verify_execution_start_state_v0(repo_root=repo_root)
    if not start_state.valid:
        raise ValueError(f"START_STATE_INVALID:{start_state.fail_reasons}")

    from datetime import datetime, timezone

    from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
        parity_status_counts_v0,
    )

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_root = (
        durable_evidence_root
        / DURABLE_EVIDENCE_SUBDIR
        / f"{DURABLE_EVIDENCE_BUNDLE_PREFIX}_{ts_slug}"
    )
    evidence_root.mkdir(parents=True, exist_ok=False)

    parity_counts = parity_status_counts_v0()
    diagnostic_output = build_diagnostic_output_v0(
        owner_policy=start_state.owner_policy,
        parity_status_counts=parity_counts,
    )

    (evidence_root / "OWNER_POLICY.json").write_text(
        json.dumps(start_state.owner_policy, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "DIAGNOSTIC_OUTPUT.json").write_text(
        json.dumps(diagnostic_output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "WORKTREE_TOLERANCE.json").write_text(
        json.dumps(
            {
                "tolerated_untracked_paths": list(start_state.tolerated_untracked_paths),
                "tolerated_untracked_artefacts": sorted(DIAGNOSTIC_TOLERATED_UNTRACKED_PATHS),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_root / "AUTHORITY_BOUNDARY_STATEMENT.md").write_text(
        "\n".join(
            [
                "# Authority Boundary Statement",
                "",
                "- status=SYSTEM_DIAGNOSTIC_ONLY",
                "- promotion_admissible=false",
                "- runtime_admissible=false",
                "- live_authorized=false",
                "- orders_allowed=false",
                "- economic_validity_claim_allowed=false",
                "- NO_RUNTIME / NO_ORDERS / NO_CREDENTIALS / NO_SCHEDULER",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    from scripts.ops import primary_evidence_retention_v0 as retention

    manifest_rc, _msg = retention.finalize_durable_bundle_manifest(evidence_root)

    return DiagnosticExecutionResultV0(
        status=diagnostic_output["status"],
        promotion_admissible=False,
        runtime_admissible=False,
        live_authorized=False,
        orders_allowed=False,
        economic_validity_claim_allowed=False,
        system_economic_evidence_admissible=False,
        scheduler_runtime_allowed=False,
        shadow_authorized=False,
        paper_authorized=False,
        testnet_authorized=False,
        canary_authorized=False,
        credential_access_allowed=False,
        promotion_boundary_status=PROMOTION_BOUNDARY_STATUS,
        promotion_boundary_reason_codes=PROMOTION_BOUNDARY_REASON_CODES,
        owner_policy_decision_digest=str(
            start_state.owner_policy.get("owner_policy_decision_digest", "")
        ),
        evidence_class_id=EVIDENCE_CLASS_ID,
        parity_status_counts=dict(parity_counts),
        evidence_root=evidence_root,
        manifest_verify_rc=manifest_rc,
    )


__all__ = [
    "DIAGNOSTIC_STATUS",
    "DIAGNOSTIC_TOLERATED_UNTRACKED_PATHS",
    "EVIDENCE_CLASS_ID",
    "CONFIRM_GO",
    "OWNER_POLICY_REL",
    "PURPOSE",
    "REASON_OWNER_POLICY_DIGEST_MISMATCH",
    "REASON_UNMODIFIED_BINDING_RETRY_BLOCKED",
    "REASON_WORKTREE_NOT_CLEAN",
    "DiagnosticExecutionResultV0",
    "StartStateVerificationResultV0",
    "build_diagnostic_output_v0",
    "compute_owner_policy_decision_digest_v0",
    "is_worktree_clean_for_diagnostic_evidence_class_v0",
    "list_non_tolerated_untracked_paths_v0",
    "list_tolerated_untracked_paths_v0",
    "run_diagnostic_evaluation_v0",
    "verify_execution_start_state_v0",
    "verify_historical_negative_evidence_immutable_v0",
    "verify_owner_policy_for_unmodified_retry_exception_v0",
    "verify_owner_policy_v0",
    "verify_unmodified_retry_for_diagnostic_evidence_class_v0",
]
