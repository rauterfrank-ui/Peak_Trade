"""Execution authorization supersession v1 for momentum_1h/v2 offline economic evaluation.

Supersedes the consumed V0 execution GO token with V1 after the fail-closed dispatch
defect execution. Does not execute evaluation and has no runtime effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.momentum_1h_v2_offline_economic_evaluation_authorization_ratification_v0 import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_STATUS,
    AUTHORITY_EFFECT,
    CONFIG_REL_PATH as AUTHORIZATION_RATIFICATION_CONFIG_REL_PATH,
    RESEARCH_SCOPE,
    RUNTIME_EFFECT,
    STRATEGY_ID,
    STRATEGY_VERSION,
)
from src.research.momentum_1h_v2_versioned_research_binding_v0 import (
    EXPECTED_BINDING_DIGEST,
    materialize_versioned_research_binding_v0,
)

PACKAGE_MARKER = (
    "MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_AUTHORIZATION_SUPERSESSION_V1=true"
)

SCHEMA_VERSION = (
    "momentum_1h_v2_offline_economic_evaluation_execution_authorization_supersession.v1"
)
SUPERSESSION_ID = (
    "momentum_1h_v2_offline_economic_evaluation_execution_authorization_supersession_v1"
)
SUPERSESSION_VERSION = "v1"
CANONICAL_SERIALIZATION_VERSION = "execution_authorization_supersession_canonical_json_v1"

CONFIG_REL_PATH = (
    "config/research/"
    "momentum_1h_v2_offline_economic_evaluation_execution_authorization_supersession_v1.json"
)

EXECUTION_GO_TOKEN = "GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V1"
SUPERSEDED_EXECUTION_GO_TOKEN = "GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
SUPERSESSION_REASON = "PRIOR_TOKEN_CONSUMED_BY_FAIL_CLOSED_EXECUTION_DEFECT"
AUTHORIZED_SCOPE = "OFFLINE_ECONOMIC_EVALUATION_EXECUTION"
NEXT_OPERATOR_GO = EXECUTION_GO_TOKEN
NEXT_RECOMMENDED_SCOPE = "MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V1"

DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
FAILED_V0_EXECUTION_BUNDLE = (
    f"{DEFAULT_ARCHIVE_ROOT}/research/"
    "momentum_1h_v2_offline_economic_evaluation_execution_v0_20260715T164131Z"
)
V1_FAILED_START_BUNDLE = (
    f"{DEFAULT_ARCHIVE_ROOT}/research/"
    "momentum_1h_v2_offline_economic_evaluation_execution_v1_20260715T171245Z"
)
SUPERSEDED_AUTHORIZATION_CONFIG_REF = AUTHORIZATION_RATIFICATION_CONFIG_REL_PATH

REASON_SUPERSESSION_MISSING = "EXECUTION_AUTHORIZATION_SUPERSESSION_MISSING"
REASON_SUPERSESSION_INVALID = "EXECUTION_AUTHORIZATION_SUPERSESSION_INVALID"
REASON_SUPERSEDED_EXECUTION_GO_TOKEN_REJECTED = "SUPERSEDED_EXECUTION_GO_TOKEN_REJECTED"
REASON_PRIOR_PRODUCTIVE_V1_EXECUTION_EXISTS = "PRIOR_PRODUCTIVE_V1_EXECUTION_EXISTS"
REASON_V0_REUSE_FORBIDDEN = "V0_REUSE_FORBIDDEN"
REASON_NEXT_OPERATOR_GO_MISMATCH = "NEXT_OPERATOR_GO_MISMATCH"


class SupersessionValidationVerdict(str, Enum):
    ACCEPTED_COMPLETE = "ACCEPTED_COMPLETE"
    REJECTED_INCOMPLETE = "REJECTED_INCOMPLETE"


@dataclass(frozen=True)
class ExecutionReplayGuardResultV1:
    allowed: bool
    v0_consumed: bool
    v0_reuse_rejected: bool
    prior_productive_v1_execution_exists: bool
    prior_v1_bundle_paths: tuple[str, ...]
    reason_codes: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_supersession_digest_v1(supersession: Mapping[str, Any]) -> str:
    return _stable_digest(
        {
            "authorized_candidate": supersession.get("authorized_candidate"),
            "authorized_scope": supersession.get("authorized_scope"),
            "binding_digest": supersession.get("binding_digest"),
            "next_operator_go": supersession.get("next_operator_go"),
            "superseded_execution_go_token": supersession.get("superseded_execution_go_token"),
            "supersession_reason": supersession.get("supersession_reason"),
        }
    )


def build_execution_authorization_supersession_contract_v1(
    *,
    versioned_binding: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "authorized_candidate": RESEARCH_SCOPE,
        "authorized_scope": AUTHORIZED_SCOPE,
        "authority_effect": AUTHORITY_EFFECT,
        "authorization_status": AUTHORIZATION_STATUS,
        "binding_digest": versioned_binding["binding_digest"],
        "economic_evaluation_executed": False,
        "failed_execution_retry_allowed": False,
        "next_operator_go": NEXT_OPERATOR_GO,
        "next_recommended_scope": NEXT_RECOMMENDED_SCOPE,
        "offline_only": True,
        "operator_go": EXECUTION_GO_TOKEN,
        "productive_execution_authorized_by_this_contract": False,
        "runtime_effect": RUNTIME_EFFECT,
        "schema_version": "execution_authorization_supersession_contract.v1",
        "scope_id": RESEARCH_SCOPE,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "superseded_authorization_config_ref": SUPERSEDED_AUTHORIZATION_CONFIG_REF,
        "superseded_execution_go_token": SUPERSEDED_EXECUTION_GO_TOKEN,
        "supersession_reason": SUPERSESSION_REASON,
        "unchanged_v0_reuse_allowed": False,
    }


def materialize_execution_authorization_supersession_v1(
    *,
    repo_root: Path | None = None,
    versioned_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    binding = dict(
        versioned_binding
        if versioned_binding is not None
        else materialize_versioned_research_binding_v0(repo_root=repo_root)
    )
    contract = build_execution_authorization_supersession_contract_v1(versioned_binding=binding)
    body: dict[str, Any] = {
        "artifact_kind": "momentum_1h_v2_offline_economic_evaluation_execution_authorization_supersession",
        "artifact_version": SUPERSESSION_VERSION,
        "authority_effect": AUTHORITY_EFFECT,
        "authorized_candidate": RESEARCH_SCOPE,
        "authorized_scope": AUTHORIZED_SCOPE,
        "authorization_status": AUTHORIZATION_STATUS,
        "binding_digest": binding["binding_digest"],
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
        "economic_evaluation_executed": False,
        "execution_authorization_supersession_contract": contract,
        "failed_execution_retry_allowed": False,
        "failed_v0_execution_bundle": FAILED_V0_EXECUTION_BUNDLE,
        "next_operator_go": NEXT_OPERATOR_GO,
        "next_recommended_scope": NEXT_RECOMMENDED_SCOPE,
        "offline_only": True,
        "productive_execution_authorized_by_this_contract": False,
        "runtime_effect": RUNTIME_EFFECT,
        "schema_version": SCHEMA_VERSION,
        "scope_id": RESEARCH_SCOPE,
        "status": "EXECUTION_AUTHORIZATION_SUPERSESSION_COMPLETE",
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "superseded_authorization_config_ref": SUPERSEDED_AUTHORIZATION_CONFIG_REF,
        "superseded_execution_go_token": SUPERSEDED_EXECUTION_GO_TOKEN,
        "supersession_id": SUPERSESSION_ID,
        "supersession_reason": SUPERSESSION_REASON,
        "supersession_version": SUPERSESSION_VERSION,
        "unchanged_v0_reuse_allowed": False,
        "v1_failed_start_bundle": V1_FAILED_START_BUNDLE,
        "verdict": "PASS",
    }
    body["supersession_digest"] = compute_supersession_digest_v1(body)
    return body


def load_execution_authorization_supersession_v1(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONFIG_REL_PATH
    if not path.is_file():
        raise FileNotFoundError(f"missing_execution_authorization_supersession:{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_execution_authorization_supersession_v1(
    supersession: Mapping[str, Any],
    *,
    expected_binding_digest: str = EXPECTED_BINDING_DIGEST,
) -> tuple[SupersessionValidationVerdict, tuple[str, ...]]:
    reasons: list[str] = []
    if supersession.get("schema_version") != SCHEMA_VERSION:
        reasons.append("SCHEMA_VERSION_MISMATCH")
    if supersession.get("authorized_candidate") != RESEARCH_SCOPE:
        reasons.append("AUTHORIZED_CANDIDATE_MISMATCH")
    if supersession.get("authorized_scope") != AUTHORIZED_SCOPE:
        reasons.append("AUTHORIZED_SCOPE_MISMATCH")
    if supersession.get("authorization_status") != AUTHORIZATION_STATUS:
        reasons.append("AUTHORIZATION_STATUS_MISMATCH")
    if supersession.get("next_operator_go") != NEXT_OPERATOR_GO:
        reasons.append(REASON_NEXT_OPERATOR_GO_MISMATCH)
    if supersession.get("superseded_execution_go_token") != SUPERSEDED_EXECUTION_GO_TOKEN:
        reasons.append("SUPERSEDED_EXECUTION_GO_TOKEN_MISMATCH")
    if supersession.get("supersession_reason") != SUPERSESSION_REASON:
        reasons.append("SUPERSESSION_REASON_MISMATCH")
    if supersession.get("unchanged_v0_reuse_allowed") is not False:
        reasons.append("UNCHANGED_V0_REUSE_ALLOWED_FORBIDDEN")
    if supersession.get("failed_execution_retry_allowed") is not False:
        reasons.append("FAILED_EXECUTION_RETRY_ALLOWED_FORBIDDEN")
    if supersession.get("productive_execution_authorized_by_this_contract") is not False:
        reasons.append("PRODUCTIVE_EXECUTION_AUTHORIZED_BY_THIS_CONTRACT_FORBIDDEN")
    if supersession.get("economic_evaluation_executed") is not False:
        reasons.append("ECONOMIC_EVALUATION_EXECUTED_MUST_BE_FALSE")
    if supersession.get("binding_digest") != expected_binding_digest:
        reasons.append("BINDING_DIGEST_MISMATCH")
    expected_digest = compute_supersession_digest_v1(supersession)
    if supersession.get("supersession_digest") != expected_digest:
        reasons.append("SUPERSESSION_DIGEST_MISMATCH")
    contract = supersession.get("execution_authorization_supersession_contract", {})
    if not isinstance(contract, Mapping):
        reasons.append("EXECUTION_AUTHORIZATION_SUPERSESSION_CONTRACT_MISSING")
    elif contract.get("next_operator_go") != NEXT_OPERATOR_GO:
        reasons.append("CONTRACT_NEXT_OPERATOR_GO_MISMATCH")
    verdict = (
        SupersessionValidationVerdict.ACCEPTED_COMPLETE
        if not reasons
        else SupersessionValidationVerdict.REJECTED_INCOMPLETE
    )
    return verdict, tuple(reasons)


def _bundle_productive_v1_execution(path: Path) -> bool:
    result_path = path / "execution_result.json"
    if result_path.is_file():
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        if payload.get("productive_economic_evaluation_executed") is True:
            return True
        if payload.get("cli_accepted_go_token") is False:
            return False
    final_report = path / "final_report.txt"
    if final_report.is_file():
        text = final_report.read_text(encoding="utf-8")
        if "PRODUCTIVE_ECONOMIC_EVALUATION_EXECUTED=true" in text:
            return True
    return False


def scan_prior_productive_v1_execution_bundles_v1(
    *,
    archive_root: Path | None = None,
) -> tuple[str, ...]:
    root = archive_root or DEFAULT_ARCHIVE_ROOT
    research = root / "research"
    if not research.is_dir():
        return ()
    bundles: list[str] = []
    for path in sorted(research.glob("momentum_1h_v2_offline_economic_evaluation_execution_v1_*")):
        if not path.is_dir():
            continue
        if _bundle_productive_v1_execution(path):
            bundles.append(str(path))
    return tuple(bundles)


def verify_v0_execution_consumed_v1(
    *,
    archive_root: Path | None = None,
    failed_v0_bundle: str = FAILED_V0_EXECUTION_BUNDLE,
) -> tuple[bool, str]:
    bundle = Path(failed_v0_bundle)
    if archive_root is not None:
        bundle = archive_root / "research" / bundle.name
    if not bundle.is_dir():
        return False, "FAILED_V0_EXECUTION_BUNDLE_MISSING"
    manifest = bundle / "MANIFEST.sha256"
    if not manifest.is_file():
        return False, "FAILED_V0_EXECUTION_MANIFEST_MISSING"
    return True, str(bundle)


def verify_execution_go_token_replay_guard_v1(
    *,
    go_token: str | None,
    archive_root: Path | None = None,
) -> ExecutionReplayGuardResultV1:
    reasons: list[str] = []
    if go_token == SUPERSEDED_EXECUTION_GO_TOKEN:
        reasons.append(REASON_SUPERSEDED_EXECUTION_GO_TOKEN_REJECTED)
        reasons.append(REASON_V0_REUSE_FORBIDDEN)
    elif go_token != EXECUTION_GO_TOKEN:
        reasons.append("GO_TOKEN_INVALID")

    v0_consumed, v0_ref = verify_v0_execution_consumed_v1(archive_root=archive_root)
    v0_reuse_rejected = go_token == SUPERSEDED_EXECUTION_GO_TOKEN or (
        go_token != EXECUTION_GO_TOKEN and go_token is not None
    )
    prior_v1 = scan_prior_productive_v1_execution_bundles_v1(archive_root=archive_root)
    if prior_v1 and go_token == EXECUTION_GO_TOKEN:
        reasons.append(REASON_PRIOR_PRODUCTIVE_V1_EXECUTION_EXISTS)

    allowed = not reasons
    return ExecutionReplayGuardResultV1(
        allowed=allowed,
        v0_consumed=v0_consumed,
        v0_reuse_rejected=v0_reuse_rejected or go_token == SUPERSEDED_EXECUTION_GO_TOKEN,
        prior_productive_v1_execution_exists=bool(prior_v1),
        prior_v1_bundle_paths=prior_v1,
        reason_codes=tuple(dict.fromkeys(reasons)),
    )


def execution_token_contract_parity_v1(
    *,
    repo_root: Path,
) -> dict[str, Any]:
    from src.research.momentum_1h_v2_offline_economic_evaluation_execution_v0 import (  # noqa: PLC0415
        EXECUTION_GO_TOKEN as HARNESS_EXECUTION_GO_TOKEN,
    )
    from scripts.ops.run_momentum_1h_v2_offline_economic_evaluation_execution_v0 import (  # noqa: PLC0415
        EXECUTION_GO as CLI_EXECUTION_GO,
    )

    supersession = load_execution_authorization_supersession_v1(repo_root)
    return {
        "authorization_next_operator_go": supersession.get("next_operator_go"),
        "cli_required_go_token": CLI_EXECUTION_GO,
        "expected_next_execution_go_token": EXECUTION_GO_TOKEN,
        "harness_execution_go_token": HARNESS_EXECUTION_GO_TOKEN,
        "token_contract_parity_pass": (
            supersession.get("next_operator_go") == EXECUTION_GO_TOKEN
            and HARNESS_EXECUTION_GO_TOKEN == EXECUTION_GO_TOKEN
            and CLI_EXECUTION_GO == EXECUTION_GO_TOKEN
        ),
    }


__all__ = [
    "AUTHORIZED_SCOPE",
    "CONFIG_REL_PATH",
    "DEFAULT_ARCHIVE_ROOT",
    "EXECUTION_GO_TOKEN",
    "FAILED_V0_EXECUTION_BUNDLE",
    "NEXT_OPERATOR_GO",
    "REASON_PRIOR_PRODUCTIVE_V1_EXECUTION_EXISTS",
    "REASON_SUPERSEDED_EXECUTION_GO_TOKEN_REJECTED",
    "REASON_V0_REUSE_FORBIDDEN",
    "SUPERSEDED_EXECUTION_GO_TOKEN",
    "SUPERSESSION_REASON",
    "ExecutionReplayGuardResultV1",
    "SupersessionValidationVerdict",
    "build_execution_authorization_supersession_contract_v1",
    "compute_supersession_digest_v1",
    "execution_token_contract_parity_v1",
    "load_execution_authorization_supersession_v1",
    "materialize_execution_authorization_supersession_v1",
    "scan_prior_productive_v1_execution_bundles_v1",
    "validate_execution_authorization_supersession_v1",
    "verify_execution_go_token_replay_guard_v1",
    "verify_v0_execution_consumed_v1",
]
