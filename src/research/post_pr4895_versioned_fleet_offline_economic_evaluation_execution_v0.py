"""Post-PR4895 versioned fleet offline economic evaluation execution v0.

Deterministic, fail-closed offline execution for
POST_PR4895_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0 using ratified
v4 fleet bindings from post-PR4895 binding ratification. Reuses canonical STEP31F owners,
panel sequential signal-density adapter, and economic viability evidence runner.
No runtime, order, or authority effect.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.backtest.economic_viability_evidence_v1 import (
    ARTIFACT_FILENAME,
    EconomicViabilityEvidenceError,
    load_economic_viability_evidence_bundle_v1,
)
from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    CandidateExecutionResultV0,
    CandidateTerminalStatus,
    FleetTerminalStatus,
    ORDER_EFFECT,
    REASON_GO_TOKEN_INVALID,
    REASON_ORIGIN_MAIN_MISMATCH,
    RUNTIME_EFFECT,
    dumps_execution_canonical_v1,
    materialize_fleet_evaluation_summary_v0,
    resolve_fleet_terminal_status_v0,
    verify_unmodified_retry_admissibility_v0,
)
from src.research.panel_sequential_signal_density_research_adapter_v0 import (
    build_sparse_signal_runtime_step31f_config_v0,
    compute_sparse_signal_density_metrics_v0,
    resolve_panel_staging_root,
)
from src.research.post_pr4895_versioned_fleet_binding_ratification_v0 import (
    CONFIG_REL_PATH as BINDING_COMPLETION_REL,
    NEXT_EXECUTION_GO,
    PROCESS_CLASSIFICATION as BINDING_PROCESS_CLASSIFICATION,
    STRATEGY_VERSION,
    ValidationVerdict as BindingValidationVerdict,
    validate_post_pr4895_versioned_fleet_binding_ratification_v0,
)
from src.research.post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0 import (
    RESEARCH_CANDIDATES,
)
from src.research.versioned_final_fleet_bindings_offline_economic_evaluation_v0 import (
    _run_candidate_with_runtime_config_v0,
)

PACKAGE_MARKER = "POST_PR4895_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0=true"

SCHEMA_VERSION = "post_pr4895_versioned_fleet_offline_economic_evaluation_execution.v0"
EXECUTION_ID = "post_pr4895_versioned_fleet_offline_economic_evaluation_execution_v0"
CANONICAL_SERIALIZATION_VERSION = "research_post_pr4895_execution_canonical_json_v1"

CONFIRM_GO = NEXT_EXECUTION_GO
SCOPE_CLASSIFICATION = (
    "BOUNDED_VERSIONED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
)
PROCESS_CLASSIFICATION = "POST_PR4895_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
EXPECTED_ORIGIN_MAIN_SHA = "523794bae4041fbd5d78fe400ff9e1e01022a510"

EXECUTION_SCOPE_REL = "config/research/post_pr4895_versioned_fleet_offline_economic_evaluation_execution_scope_v0.json"
GOVERNANCE_REL_PATH = (
    "docs/governance/POST_PR4895_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0.md"
)

BINDING_COMPLETION_DIGEST = "40f28451eccb2bd95c26520ba0f3f51325aaaefd0273de61f7d9b035ac4a661b"
EXECUTION_SCOPE_DIGEST = "cd4ccdc69edefb5c4d1f5e26d76845b5e41ec082f6b1a150b50732bac7fe7ffa"
EXECUTION_SEMANTIC_DIGEST = "0f9959b1c9b8c9907918a376ac98be61fb7ccf4238c89715fcc6d206e8f21d6f"
EVIDENCE_CLASS_ID = "POST_PR4895_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"

PARENT_BINDING_BUNDLE_SUFFIX = (
    "post_pr4895_versioned_fleet_binding_ratification_v0_20260706T021121Z"
)

DURABLE_EVIDENCE_SUBDIR = "implementation"
DURABLE_EVIDENCE_BUNDLE_PREFIX = (
    "post_pr4895_versioned_fleet_offline_economic_evaluation_execution_v0"
)

DEFAULT_DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)

REASON_EXECUTION_SCOPE_CONFIG_MISSING = "EXECUTION_SCOPE_CONFIG_MISSING"
REASON_SCOPE_BINDING_NOT_READY = "EXECUTION_SCOPE_BINDING_NOT_READY"
REASON_SCOPE_DIGEST_MISMATCH = "EXECUTION_SCOPE_DIGEST_MISMATCH"
REASON_SEMANTIC_DIGEST_MISMATCH = "EXECUTION_SEMANTIC_DIGEST_MISMATCH"
REASON_EVIDENCE_CLASS_MISMATCH = "EVIDENCE_CLASS_ID_MISMATCH"
REASON_COMPLETION_DIGEST_MISMATCH = "BINDING_COMPLETION_DIGEST_MISMATCH"
REASON_EVALUATION_ALREADY_EXECUTED = "ECONOMIC_EVALUATION_ALREADY_EXECUTED"
REASON_WORKTREE_DIRTY = "WORKTREE_NOT_CLEAN"
REASON_BINDING_STATUS_INVALID = "POST_PR4895_BINDING_STATUS_INVALID"
REASON_PARENT_MANIFEST_INVALID = "PARENT_BINDING_BUNDLE_MANIFEST_INVALID"


class CandidateEconomicVerdict(str, Enum):
    ECONOMICALLY_VIABLE_OFFLINE = "ECONOMICALLY_VIABLE_OFFLINE"
    ROBUSTNESS_FAILED = "ROBUSTNESS_FAILED"
    ECONOMIC_VALIDITY_FAILED = "ECONOMIC_VALIDITY_FAILED"
    INCONCLUSIVE_EXECUTION_GAP = "INCONCLUSIVE_EXECUTION_GAP"
    BLOCKED_BINDING_OR_EVIDENCE_GAP = "BLOCKED_BINDING_OR_EVIDENCE_GAP"


class FleetEconomicVerdict(str, Enum):
    FLEET_ECONOMIC_VALIDITY_PASS = "FLEET_ECONOMIC_VALIDITY_PASS"
    FLEET_ECONOMIC_VALIDITY_FAIL = "FLEET_ECONOMIC_VALIDITY_FAIL"
    FLEET_ECONOMIC_VALIDITY_INCONCLUSIVE = "FLEET_ECONOMIC_VALIDITY_INCONCLUSIVE"
    FLEET_EXECUTION_BLOCKED_FAIL_CLOSED = "FLEET_EXECUTION_BLOCKED_FAIL_CLOSED"


@dataclass(frozen=True)
class StartStateVerificationResultV0:
    valid: bool
    fail_reasons: tuple[str, ...]
    origin_main_sha: str
    execution_scope: dict[str, Any]
    binding_completion: dict[str, Any]
    parent_manifest_verify_rc: int


@dataclass(frozen=True)
class ScopeExecutionResultV0:
    execution_scope: dict[str, Any]
    binding_completion: dict[str, Any]
    candidate_results: tuple[CandidateExecutionResultV0, ...]
    candidate_verdicts: dict[str, CandidateEconomicVerdict]
    sparse_signal_metrics: dict[str, dict[str, Any]]
    fleet_verdict: FleetEconomicVerdict
    fleet_status: FleetTerminalStatus
    economic_validity_offline_gate_pass: bool
    manifest_verify_rc: int
    evidence_root: Path
    process_classification: str


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _resolve_origin_main_sha(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "origin/main"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _worktree_dirty_count(repo_root: Path) -> int:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    return len([line for line in result.stdout.splitlines() if line.strip()])


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"not_object:{path}")
    return payload


def _metric_value(payload: Mapping[str, Any], field: str) -> Any:
    raw = payload.get(field)
    if isinstance(raw, Mapping):
        return raw.get("value")
    return raw


def compute_execution_scope_digests_v0(scope_body: Mapping[str, Any]) -> tuple[str, str]:
    scope_fields = {
        k: v
        for k, v in scope_body.items()
        if k
        not in (
            "scope_digest",
            "semantic_digest",
            "execution_performed",
            "execution_completed_at_utc",
            "fleet_verdict",
            "fleet_status",
            "economic_validity_offline_gate_pass",
            "durable_evidence_ref",
        )
    }
    semantic_fields = {
        "binding_class": scope_body.get("binding_class"),
        "binding_completion_digest": scope_body.get("binding_completion_digest"),
        "evidence_class_id": scope_body.get("evidence_class_id"),
        "execution_go_token": scope_body.get("execution_go_token"),
        "fleet_candidates": scope_body.get("fleet_candidates"),
        "parent_binding_bundle_suffix": scope_body.get("parent_binding_bundle_suffix"),
        "retry_unchanged_binding_allowed": scope_body.get("retry_unchanged_binding_allowed"),
        "scope_classification": scope_body.get("scope_classification"),
        "strategy_version": scope_body.get("strategy_version"),
    }
    return _stable_digest(scope_fields), _stable_digest(semantic_fields)


def classify_candidate_verdict_v0(
    result: CandidateExecutionResultV0,
    *,
    evidence_payload: Mapping[str, Any],
) -> CandidateEconomicVerdict:
    if result.manifest_verify_rc != 0:
        return CandidateEconomicVerdict.BLOCKED_BINDING_OR_EVIDENCE_GAP
    if not result.runner_execution_success:
        return CandidateEconomicVerdict.INCONCLUSIVE_EXECUTION_GAP
    if result.terminal_status is CandidateTerminalStatus.INCONCLUSIVE:
        return CandidateEconomicVerdict.INCONCLUSIVE_EXECUTION_GAP
    status = str(evidence_payload.get("status") or result.evidence_status or "")
    if status == CandidateEconomicVerdict.ECONOMICALLY_VIABLE_OFFLINE.value:
        return CandidateEconomicVerdict.ECONOMICALLY_VIABLE_OFFLINE
    if (
        status == CandidateEconomicVerdict.ROBUSTNESS_FAILED.value
        or result.terminal_status is CandidateTerminalStatus.FAIL
    ):
        return CandidateEconomicVerdict.ROBUSTNESS_FAILED
    if status in {"RESEARCH_ONLY", "PROMISING"}:
        return CandidateEconomicVerdict.ECONOMIC_VALIDITY_FAILED
    if not evidence_payload:
        return CandidateEconomicVerdict.BLOCKED_BINDING_OR_EVIDENCE_GAP
    return CandidateEconomicVerdict.INCONCLUSIVE_EXECUTION_GAP


def classify_fleet_verdict_v0(
    candidate_verdicts: Sequence[CandidateEconomicVerdict],
) -> FleetEconomicVerdict:
    if any(
        v is CandidateEconomicVerdict.BLOCKED_BINDING_OR_EVIDENCE_GAP for v in candidate_verdicts
    ):
        return FleetEconomicVerdict.FLEET_EXECUTION_BLOCKED_FAIL_CLOSED
    if any(v is CandidateEconomicVerdict.INCONCLUSIVE_EXECUTION_GAP for v in candidate_verdicts):
        return FleetEconomicVerdict.FLEET_ECONOMIC_VALIDITY_INCONCLUSIVE
    if all(v is CandidateEconomicVerdict.ECONOMICALLY_VIABLE_OFFLINE for v in candidate_verdicts):
        return FleetEconomicVerdict.FLEET_ECONOMIC_VALIDITY_PASS
    return FleetEconomicVerdict.FLEET_ECONOMIC_VALIDITY_FAIL


def verify_preconditions_v0(
    *,
    repo_root: Path,
    confirm: str,
    origin_main_sha: str | None = None,
    require_clean_worktree: bool = True,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if confirm != CONFIRM_GO:
        reasons.append(REASON_GO_TOKEN_INVALID)
    resolved = origin_main_sha or _resolve_origin_main_sha(repo_root)
    if resolved != EXPECTED_ORIGIN_MAIN_SHA:
        reasons.append(f"{REASON_ORIGIN_MAIN_MISMATCH}:{resolved}")
    if require_clean_worktree and _worktree_dirty_count(repo_root) > 0:
        reasons.append(REASON_WORKTREE_DIRTY)
    return not reasons, tuple(reasons)


def verify_parent_binding_bundle_manifest_v0(
    *,
    durable_evidence_root: Path,
) -> tuple[int, str]:
    from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256

    parent_dir = durable_evidence_root / DURABLE_EVIDENCE_SUBDIR / PARENT_BINDING_BUNDLE_SUFFIX
    ok, msg = verify_manifest_sha256(parent_dir)
    return (0 if ok else 1), msg or "ok"


def verify_execution_scope_v0(
    scope: Mapping[str, Any],
    *,
    binding_completion: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if scope.get("binding_ready") is not True:
        reasons.append(REASON_SCOPE_BINDING_NOT_READY)
    if str(scope.get("scope_digest", "")) != EXECUTION_SCOPE_DIGEST:
        reasons.append(REASON_SCOPE_DIGEST_MISMATCH)
    if str(scope.get("semantic_digest", "")) != EXECUTION_SEMANTIC_DIGEST:
        reasons.append(REASON_SEMANTIC_DIGEST_MISMATCH)
    if str(scope.get("binding_completion_digest", "")) != BINDING_COMPLETION_DIGEST:
        reasons.append(REASON_COMPLETION_DIGEST_MISMATCH)
    if str(scope.get("evidence_class_id", "")) != EVIDENCE_CLASS_ID:
        reasons.append(REASON_EVIDENCE_CLASS_MISMATCH)
    if str(scope.get("execution_go_token", "")) != CONFIRM_GO:
        reasons.append("EXECUTION_CONFIRM_GO_MISMATCH")
    if scope.get("retry_unchanged_binding_allowed") is not False:
        reasons.append("RETRY_UNCHANGED_BINDING_MUST_BE_FALSE")
    if str(scope.get("parent_binding_bundle_suffix", "")) != PARENT_BINDING_BUNDLE_SUFFIX:
        reasons.append("PARENT_BINDING_BUNDLE_SUFFIX_MISMATCH")
    completion_digest = str(binding_completion.get("completion_digest", ""))
    if completion_digest != BINDING_COMPLETION_DIGEST:
        reasons.append(f"{REASON_COMPLETION_DIGEST_MISMATCH}:{completion_digest}")
    retry_ok, retry_reasons = verify_unmodified_retry_admissibility_v0(
        fleet_binding_completion=binding_completion,
        requested_execution_evidence_class=EVIDENCE_CLASS_ID,
    )
    if not retry_ok:
        reasons.extend(retry_reasons)
    return not reasons, tuple(reasons)


def verify_execution_start_state_v0(
    *,
    repo_root: Path,
    durable_evidence_root: Path,
    require_clean_worktree: bool = True,
) -> StartStateVerificationResultV0:
    reasons: list[str] = []
    origin_main = _resolve_origin_main_sha(repo_root)
    pre_ok, pre_reasons = verify_preconditions_v0(
        repo_root=repo_root,
        confirm=CONFIRM_GO,
        origin_main_sha=origin_main,
        require_clean_worktree=require_clean_worktree,
    )
    if not pre_ok:
        reasons.extend(pre_reasons)

    scope_path = repo_root / EXECUTION_SCOPE_REL
    binding_path = repo_root / BINDING_COMPLETION_REL
    if not scope_path.is_file():
        reasons.append(REASON_EXECUTION_SCOPE_CONFIG_MISSING)
    if not binding_path.is_file():
        reasons.append("POST_PR4895_BINDING_COMPLETION_MISSING")

    execution_scope: dict[str, Any] = {}
    binding_completion: dict[str, Any] = {}
    if scope_path.is_file():
        execution_scope = _load_json(scope_path)
    if binding_path.is_file():
        binding_completion = _load_json(binding_path)

    parent_manifest_rc, parent_msg = verify_parent_binding_bundle_manifest_v0(
        durable_evidence_root=durable_evidence_root,
    )
    if parent_manifest_rc != 0:
        reasons.append(f"{REASON_PARENT_MANIFEST_INVALID}:{parent_msg}")

    if binding_completion.get("status") != "FLEET_BINDINGS_RATIFIED_NOT_EVALUATED":
        reasons.append(REASON_BINDING_STATUS_INVALID)
    if binding_completion.get("economic_evaluation_executed") is not False:
        reasons.append(REASON_EVALUATION_ALREADY_EXECUTED)

    if execution_scope.get("execution_performed") is True:
        reasons.append(REASON_EVALUATION_ALREADY_EXECUTED)

    if execution_scope and binding_completion:
        scope_ok, scope_reasons = verify_execution_scope_v0(
            execution_scope,
            binding_completion=binding_completion,
        )
        if not scope_ok:
            reasons.extend(scope_reasons)

    if binding_completion:
        validation = validate_post_pr4895_versioned_fleet_binding_ratification_v0(
            binding_completion
        )
        if validation.verdict != BindingValidationVerdict.ACCEPTED:
            reasons.extend(validation.fail_reasons)

    staging_root = resolve_panel_staging_root()
    if not staging_root.is_dir():
        reasons.append("PANEL_STAGING_ROOT_MISSING")

    return StartStateVerificationResultV0(
        valid=not reasons,
        fail_reasons=tuple(reasons),
        origin_main_sha=origin_main,
        execution_scope=execution_scope,
        binding_completion=binding_completion,
        parent_manifest_verify_rc=parent_manifest_rc,
    )


def materialize_candidate_result_v0(
    *,
    strategy_id: str,
    candidate_dir: Path,
    result: CandidateExecutionResultV0,
    candidate_binding: Mapping[str, Any],
    verdict: CandidateEconomicVerdict,
    sparse_metrics: Mapping[str, Any],
    evidence_payload: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "strategy_id": strategy_id,
        "strategy_version": STRATEGY_VERSION,
        "canonical_candidate_identifier": result.canonical_candidate_identifier,
        "verdict": verdict.value,
        "sparse_signal_density_metrics": dict(sparse_metrics),
        "reason_codes": list(result.reason_codes),
        "trade_count": _metric_value(evidence_payload, "trade_count"),
        "gross_return": _metric_value(evidence_payload, "gross_return"),
        "net_return": _metric_value(evidence_payload, "net_return"),
        "net_expectancy": _metric_value(evidence_payload, "net_expectancy"),
        "profit_factor": _metric_value(evidence_payload, "profit_factor"),
        "sharpe": _metric_value(evidence_payload, "sharpe"),
        "max_drawdown": _metric_value(evidence_payload, "max_drawdown"),
        "walk_forward_results": evidence_payload.get("walk_forward_results"),
        "monte_carlo_results": evidence_payload.get("monte_carlo_results"),
        "stress_results": evidence_payload.get("stress_results"),
        "parameter_sensitivity_results": evidence_payload.get("parameter_sensitivity_results"),
        "evidence_status": evidence_payload.get("status"),
        "manifest_verify_rc": result.manifest_verify_rc,
        "output_dir": str(candidate_dir),
        "run_id": result.run_id,
        "input_bindings": {
            "strategy_id": strategy_id,
            "strategy_version": STRATEGY_VERSION,
            "parameter_binding": candidate_binding.get("parameter_binding"),
            "dataset_binding": candidate_binding.get("dataset_binding"),
            "period_binding": candidate_binding.get("period_binding"),
            "instrument_binding": candidate_binding.get("instrument_binding"),
            "fee_model_binding": candidate_binding.get("fee_model_binding"),
            "slippage_model_binding": candidate_binding.get("slippage_model_binding"),
            "funding_model_binding": candidate_binding.get("funding_model_binding"),
            "execution_model_binding": candidate_binding.get("execution_model_binding"),
            "economic_policy_binding": candidate_binding.get("economic_policy_binding"),
            "implementation_digest": candidate_binding.get("implementation_digest"),
            "config_digest": candidate_binding.get("config_digest"),
            "data_digest": candidate_binding.get("data_digest"),
        },
    }


def _write_required_bundle_artifacts_v0(
    *,
    evidence_root: Path,
    start_state: StartStateVerificationResultV0,
    candidate_records: Mapping[str, Mapping[str, Any]],
    candidate_verdicts: Mapping[str, CandidateEconomicVerdict],
    fleet_verdict: FleetEconomicVerdict,
    fleet_status: FleetTerminalStatus,
    gate_pass: bool,
) -> None:
    for strategy_id in RESEARCH_CANDIDATES:
        record = candidate_records.get(strategy_id, {})
        (evidence_root / f"CANDIDATE_RESULT_{strategy_id}.json").write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        candidate_dir = Path(str(record.get("output_dir", "")))
        evidence_src = candidate_dir / ARTIFACT_FILENAME
        if evidence_src.is_file():
            shutil.copy2(
                evidence_src,
                evidence_root / f"ECONOMIC_VIABILITY_EVIDENCE_{strategy_id}.json",
            )
        wf = record.get("walk_forward_results")
        if wf is not None:
            (evidence_root / f"WALK_FORWARD_RESULTS_{strategy_id}.json").write_text(
                json.dumps(wf, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        mc = record.get("monte_carlo_results")
        if mc is not None:
            (evidence_root / f"MONTE_CARLO_RESULTS_{strategy_id}.json").write_text(
                json.dumps(mc, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        stress = record.get("stress_results")
        if stress is not None:
            (evidence_root / f"STRESS_RESULTS_{strategy_id}.json").write_text(
                json.dumps(stress, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        ps = record.get("parameter_sensitivity_results")
        if ps is not None:
            (evidence_root / f"PARAMETER_SENSITIVITY_RESULTS_{strategy_id}.json").write_text(
                json.dumps(ps, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

    fleet_summary = {
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "go_token_consumed": CONFIRM_GO,
        "origin_main_sha": start_state.origin_main_sha,
        "binding_completion_digest": BINDING_COMPLETION_DIGEST,
        "parent_binding_bundle_suffix": PARENT_BINDING_BUNDLE_SUFFIX,
        "parent_manifest_verify_rc": start_state.parent_manifest_verify_rc,
        "fleet_verdict": fleet_verdict.value,
        "fleet_status": fleet_status.value,
        "economic_validity_offline_gate_pass": gate_pass,
        "candidate_verdicts": {sid: v.value for sid, v in candidate_verdicts.items()},
        "final_research_fleet": list(RESEARCH_CANDIDATES),
        "strategy_version": STRATEGY_VERSION,
        "promotion_authority": False,
        "runtime_authority": False,
        "shadow_authorized": False,
        "paper_authorized": False,
        "testnet_authorized": False,
        "live_authorized": False,
    }
    (evidence_root / "FLEET_ECONOMIC_SUMMARY.json").write_text(
        json.dumps(fleet_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "EXECUTION_REPORT.md").write_text(
        "\n".join(
            [
                "# Execution Report",
                "",
                f"- evidence_class_id: `{EVIDENCE_CLASS_ID}`",
                f"- process_classification: `{PROCESS_CLASSIFICATION}`",
                f"- scope_classification: `{SCOPE_CLASSIFICATION}`",
                f"- go_token_consumed: `{CONFIRM_GO}`",
                f"- origin_main_sha: `{start_state.origin_main_sha}`",
                f"- binding_completion_digest: `{BINDING_COMPLETION_DIGEST}`",
                f"- parent_binding_bundle: `{PARENT_BINDING_BUNDLE_SUFFIX}`",
                f"- parent_manifest_verify_rc: `{start_state.parent_manifest_verify_rc}`",
                f"- fleet_verdict: `{fleet_verdict.value}`",
                f"- fleet_status: `{fleet_status.value}`",
                f"- economic_validity_offline_gate_pass: `{gate_pass}`",
                "",
                "## Candidate verdicts",
                "",
                *[
                    f"- `{sid}`: `{candidate_verdicts[sid].value}`"
                    for sid in RESEARCH_CANDIDATES
                    if sid in candidate_verdicts
                ],
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    if not gate_pass:
        (evidence_root / "FAILURE_CLASSIFICATION.md").write_text(
            "\n".join(
                [
                    "# Failure Classification",
                    "",
                    f"- fleet_verdict: `{fleet_verdict.value}`",
                    f"- fleet_status: `{fleet_status.value}`",
                    f"- economic_validity_offline_gate_pass: `{gate_pass}`",
                    "",
                    "## Candidate verdicts",
                    "",
                    *[
                        f"- `{sid}`: `{candidate_verdicts[sid].value}`"
                        for sid in RESEARCH_CANDIDATES
                        if sid in candidate_verdicts
                    ],
                ]
            )
            + "\n",
            encoding="utf-8",
        )


def run_bounded_scope_v0(
    *,
    confirm: str,
    repo_root: Path,
    durable_evidence_root: Path,
    require_clean_worktree: bool = True,
) -> ScopeExecutionResultV0:
    pre_ok, pre_reasons = verify_preconditions_v0(
        repo_root=repo_root,
        confirm=confirm,
        require_clean_worktree=require_clean_worktree,
    )
    if not pre_ok:
        raise ValueError(f"PRECONDITION_FAILED:{pre_reasons}")

    start_state = verify_execution_start_state_v0(
        repo_root=repo_root,
        durable_evidence_root=durable_evidence_root,
        require_clean_worktree=require_clean_worktree,
    )
    if not start_state.valid:
        raise ValueError(f"START_STATE_INVALID:{start_state.fail_reasons}")

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_root = (
        durable_evidence_root
        / DURABLE_EVIDENCE_SUBDIR
        / f"{DURABLE_EVIDENCE_BUNDLE_PREFIX}_{ts_slug}"
    )
    evidence_root.mkdir(parents=True, exist_ok=False)

    execution_scope = start_state.execution_scope
    binding_completion = start_state.binding_completion
    staging_root = resolve_panel_staging_root()

    for name, payload in (
        ("execution_scope_v0.json", execution_scope),
        ("binding_ratification_v0.json", binding_completion),
    ):
        (evidence_root / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    (evidence_root / "go_token_consumption.json").write_text(
        json.dumps(
            {
                "consumed_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "go_token": CONFIRM_GO,
                "go_token_consumed": True,
                "scope_classification": SCOPE_CLASSIFICATION,
                "evidence_class_id": EVIDENCE_CLASS_ID,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    candidate_bindings = {
        str(candidate["strategy_id"]): candidate
        for candidate in binding_completion.get("candidates", [])
        if isinstance(candidate, Mapping)
    }

    candidate_results: list[CandidateExecutionResultV0] = []
    candidate_records: dict[str, dict[str, Any]] = {}
    candidate_verdicts: dict[str, CandidateEconomicVerdict] = {}
    sparse_signal_metrics: dict[str, dict[str, Any]] = {}
    scratch_root = evidence_root / "panel_signal_density_scan"

    for strategy_id in RESEARCH_CANDIDATES:
        metrics = compute_sparse_signal_density_metrics_v0(
            repo_root=repo_root,
            strategy_id=strategy_id,
            staging_root=staging_root,
            scratch_root=scratch_root / strategy_id,
        )
        sparse_signal_metrics[strategy_id] = metrics.to_dict()

        config_dir = evidence_root / "RUNTIME_STEP31F_CONFIGS"
        config_path = build_sparse_signal_runtime_step31f_config_v0(
            repo_root=repo_root,
            strategy_id=strategy_id,
            staging_root=staging_root,
            instrument_id=metrics.evaluation_instrument_id,
            output_path=config_dir
            / f"step31f_{strategy_id}_{STRATEGY_VERSION}_economic_evaluation_v1.json",
        )
        candidate_dir = evidence_root / "candidates" / f"{strategy_id}_{STRATEGY_VERSION}"
        candidate_dir.parent.mkdir(parents=True, exist_ok=True)
        result = _run_candidate_with_runtime_config_v0(
            repo_root=repo_root,
            strategy_id=strategy_id,
            strategy_version=STRATEGY_VERSION,
            config_path=config_path,
            output_dir=candidate_dir,
        )
        candidate_results.append(result)

        evidence_payload: dict[str, Any] = {}
        if (candidate_dir / ARTIFACT_FILENAME).is_file():
            try:
                loaded = load_economic_viability_evidence_bundle_v1(candidate_dir)
                evidence_payload = loaded.evidence.to_dict()
            except EconomicViabilityEvidenceError:
                evidence_payload = {}

        verdict = classify_candidate_verdict_v0(result, evidence_payload=evidence_payload)
        candidate_verdicts[strategy_id] = verdict
        binding = candidate_bindings.get(strategy_id, {})
        record = materialize_candidate_result_v0(
            strategy_id=strategy_id,
            candidate_dir=candidate_dir,
            result=result,
            candidate_binding=binding,
            verdict=verdict,
            sparse_metrics=metrics.to_dict(),
            evidence_payload=evidence_payload,
        )
        candidate_records[strategy_id] = record

    fleet_status = resolve_fleet_terminal_status_v0(candidate_results)
    fleet_verdict = classify_fleet_verdict_v0(list(candidate_verdicts.values()))
    gate_pass = fleet_verdict is FleetEconomicVerdict.FLEET_ECONOMIC_VALIDITY_PASS

    ratification_stub = {
        "operator_scope_ratification_ref": BINDING_COMPLETION_REL,
        "ratification_digest": binding_completion.get("completion_digest"),
        "fleet_binding_digest": binding_completion.get("completion_digest"),
    }
    fleet_summary = materialize_fleet_evaluation_summary_v0(
        ratification=ratification_stub,
        candidate_results=candidate_results,
        execution_bundle_dir=str(evidence_root),
        origin_main_sha=start_state.origin_main_sha,
    )
    fleet_summary["scope_classification"] = SCOPE_CLASSIFICATION
    fleet_summary["process_classification"] = PROCESS_CLASSIFICATION
    fleet_summary["go_token_consumed"] = CONFIRM_GO
    fleet_summary["evidence_class_id"] = EVIDENCE_CLASS_ID
    fleet_summary["fleet_verdict"] = fleet_verdict.value
    fleet_summary["candidate_verdicts"] = {
        sid: verdict.value for sid, verdict in candidate_verdicts.items()
    }
    fleet_summary["sparse_signal_density_metrics"] = sparse_signal_metrics
    fleet_summary["candidate_evidence_records"] = candidate_records
    fleet_summary["authority_matrix"] = {
        "candidate_ratified": False,
        "promotion_authorized": False,
        "runtime_authority": False,
        "orders_allowed": False,
    }

    (evidence_root / "fleet_evaluation_summary_v0.json").write_text(
        dumps_execution_canonical_v1(fleet_summary) + "\n",
        encoding="utf-8",
    )

    _write_required_bundle_artifacts_v0(
        evidence_root=evidence_root,
        start_state=start_state,
        candidate_records=candidate_records,
        candidate_verdicts=candidate_verdicts,
        fleet_verdict=fleet_verdict,
        fleet_status=fleet_status,
        gate_pass=gate_pass,
    )

    from scripts.ops import primary_evidence_retention_v0 as retention

    manifest_rc, _msg = retention.finalize_durable_bundle_manifest(evidence_root)

    return ScopeExecutionResultV0(
        execution_scope=execution_scope,
        binding_completion=binding_completion,
        candidate_results=tuple(candidate_results),
        candidate_verdicts=candidate_verdicts,
        sparse_signal_metrics=sparse_signal_metrics,
        fleet_verdict=fleet_verdict,
        fleet_status=fleet_status,
        economic_validity_offline_gate_pass=gate_pass,
        manifest_verify_rc=manifest_rc,
        evidence_root=evidence_root,
        process_classification=PROCESS_CLASSIFICATION,
    )


__all__ = [
    "CONFIRM_GO",
    "SCOPE_CLASSIFICATION",
    "PROCESS_CLASSIFICATION",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "BINDING_COMPLETION_DIGEST",
    "EXECUTION_SCOPE_DIGEST",
    "EXECUTION_SEMANTIC_DIGEST",
    "EVIDENCE_CLASS_ID",
    "CandidateEconomicVerdict",
    "FleetEconomicVerdict",
    "compute_execution_scope_digests_v0",
    "verify_preconditions_v0",
    "verify_execution_scope_v0",
    "verify_execution_start_state_v0",
    "run_bounded_scope_v0",
    "ScopeExecutionResultV0",
]
