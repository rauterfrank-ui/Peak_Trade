"""Post-no-pass STEP31F owner-fix offline economic evaluation execution v0.

Deterministic, fail-closed offline execution for
POST_NO_PASS_METRIC_MATERIALIZATION_PATH_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0_WITH_STEP31F_OWNER_FIX
using ratified v3 path-activation fleet bindings after the STEP31F promotion metric
materialization path execution owner narrow implementation fix. Reuses canonical STEP31F
owners, fixed panel sequential signal-density adapter, and economic viability evidence runner.
No runtime, order, or authority effect.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
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
from src.research.final_research_fleet_versioned_binding_completion_v0 import (
    canonical_candidate_identifier,
)
from src.research.panel_sequential_signal_density_research_adapter_v0 import (
    build_sparse_signal_runtime_step31f_config_v0,
    compute_sparse_signal_density_metrics_v0,
    resolve_panel_staging_root,
)
from src.research.post_no_pass_metric_materialization_path_activation_binding_ratification_v0 import (
    CONFIG_REL_PATH as PATH_ACTIVATION_BINDING_REL,
    METRIC_MATERIALIZATION_PATH_REF,
    PRIMARY_CAUSE,
    STRATEGY_VERSION,
    ValidationVerdict as PathActivationValidationVerdict,
    validate_post_no_pass_metric_materialization_path_activation_binding_ratification_v0,
)
from src.research.post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0 import (
    CONFIG_REL_PATH as SPARSE_V2_BINDING_REL,
    RESEARCH_CANDIDATES,
)
from src.research.step31f_promotion_metric_materialization_path_execution_owner_v0 import (
    materialize_promotion_metric_materialization_record_from_sparse_signal_inputs_v0,
)
from src.research.versioned_final_fleet_bindings_offline_economic_evaluation_v0 import (
    _run_candidate_with_runtime_config_v0,
)

PACKAGE_MARKER = "POST_NO_PASS_STEP31F_OWNER_FIX_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0=true"

SCHEMA_VERSION = "post_no_pass_step31f_owner_fix_offline_economic_evaluation_execution.v0"
EXECUTION_ID = "post_no_pass_step31f_owner_fix_offline_economic_evaluation_execution_v0"
CANONICAL_SERIALIZATION_VERSION = "research_metric_materialization_execution_canonical_json_v1"

CONFIRM_GO = (
    "GO_OPERATOR_AUTHORIZE_POST_NO_PASS_METRIC_MATERIALIZATION_PATH_OFFLINE_"
    "ECONOMIC_EVALUATION_EXECUTION_V0_WITH_STEP31F_OWNER_FIX"
)
SCOPE_CLASSIFICATION = (
    "POST_NO_PASS_METRIC_MATERIALIZATION_PATH_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0_"
    "WITH_STEP31F_OWNER_FIX"
)
PROCESS_CLASSIFICATION = SCOPE_CLASSIFICATION
EXPECTED_ORIGIN_MAIN_SHA = "b86a9813795e35cea1e2ca0a985d19c8f7c8ec11"

EXECUTION_SCOPE_REL = (
    "config/research/"
    "post_no_pass_step31f_owner_fix_offline_economic_evaluation_execution_scope_v0.json"
)
SCOPE_DEFINITION_REL = (
    "config/research/"
    "post_no_pass_step31f_owner_fix_offline_economic_evaluation_scope_definition_v0.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/POST_NO_PASS_STEP31F_OWNER_FIX_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0.md"
)

PATH_ACTIVATION_BINDING_COMPLETION_DIGEST = (
    "9cdb5503690131787a423c24d83aa98a34d594cb4c9a349ca94200ff2657f88d"
)
EXECUTION_SCOPE_DIGEST = "45ed8249cfaf5a69c4f7cf522fa159c1164200d26df5167cffaa53e5d09631ab"
EXECUTION_SEMANTIC_DIGEST = "a4cba8057eeb6608400fac6ee8f9f2ee9505b15cd627e93a04367194d4dcee72"
EVIDENCE_CLASS_ID = (
    "POST_NO_PASS_METRIC_MATERIALIZATION_PATH_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0_"
    "WITH_STEP31F_OWNER_FIX"
)

DURABLE_EVIDENCE_SUBDIR = "implementation"
DURABLE_EVIDENCE_BUNDLE_PREFIX = (
    "post_no_pass_step31f_owner_fix_offline_economic_evaluation_execution_v0"
)
OWNER_FIX_EVIDENCE_BUNDLE_SUFFIX = "step31f_promotion_metric_materialization_path_execution_owner_narrow_implementation_fix_scope_v0_20260706T004823Z"
PARENT_EXECUTION_EVIDENCE_BUNDLE_SUFFIX = "post_no_pass_metric_materialization_path_offline_economic_evaluation_execution_v0_20260705T235133Z"
ACTIVATION_EVIDENCE_BUNDLE_SUFFIX = (
    "post_no_pass_metric_materialization_path_activation_binding_ratification_v0_20260705T233631Z"
)
OWNER_FIX_MODULE_REF = (
    "src/research/step31f_promotion_metric_materialization_path_execution_owner_v0.py"
)

DEFAULT_DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)

REASON_EXECUTION_SCOPE_CONFIG_MISSING = "EXECUTION_SCOPE_CONFIG_MISSING"
REASON_SCOPE_DEFINITION_MISSING = "SCOPE_DEFINITION_CONFIG_MISSING"
REASON_SCOPE_DEFINITION_STATUS_INVALID = "SCOPE_DEFINITION_STATUS_INVALID"
REASON_SCOPE_DEFINITION_NEXT_GO_MISMATCH = "SCOPE_DEFINITION_NEXT_GO_MISMATCH"
REASON_SCOPE_BINDING_NOT_READY = "EXECUTION_SCOPE_BINDING_NOT_READY"
REASON_SCOPE_DIGEST_MISMATCH = "EXECUTION_SCOPE_DIGEST_MISMATCH"
REASON_SEMANTIC_DIGEST_MISMATCH = "EXECUTION_SEMANTIC_DIGEST_MISMATCH"
REASON_EVIDENCE_CLASS_MISMATCH = "EVIDENCE_CLASS_ID_MISMATCH"
REASON_COMPLETION_DIGEST_MISMATCH = "BINDING_COMPLETION_DIGEST_MISMATCH"
REASON_EVALUATION_ALREADY_EXECUTED = "ECONOMIC_EVALUATION_ALREADY_EXECUTED"
REASON_WORKTREE_DIRTY = "WORKTREE_NOT_CLEAN"
REASON_BINDING_STATUS_INVALID = "PATH_ACTIVATION_BINDING_STATUS_INVALID"
REASON_PATH_ACTIVATION_NOT_RATIFIED = "PATH_ACTIVATION_BINDING_NOT_RATIFIED"
REASON_ACTIVATION_MANIFEST_INVALID = "ACTIVATION_EVIDENCE_MANIFEST_INVALID"
REASON_OWNER_FIX_MANIFEST_INVALID = "OWNER_FIX_EVIDENCE_MANIFEST_INVALID"
REASON_PARENT_EXECUTION_MANIFEST_INVALID = "PARENT_EXECUTION_EVIDENCE_MANIFEST_INVALID"


class EconomicExecutionVerdict(str, Enum):
    ECONOMICALLY_VIABLE_OFFLINE = "ECONOMICALLY_VIABLE_OFFLINE"
    ROBUSTNESS_FAILED = "ROBUSTNESS_FAILED"
    INCONCLUSIVE_INSUFFICIENT_EVIDENCE = "INCONCLUSIVE_INSUFFICIENT_EVIDENCE"
    EXECUTION_FAILED_FAIL_CLOSED = "EXECUTION_FAILED_FAIL_CLOSED"
    METRICS_NOT_MATERIALIZED = "METRICS_NOT_MATERIALIZED"


@dataclass(frozen=True)
class StartStateVerificationResultV0:
    valid: bool
    fail_reasons: tuple[str, ...]
    origin_main_sha: str
    execution_scope: dict[str, Any]
    scope_definition: dict[str, Any]
    path_activation_binding: dict[str, Any]
    activation_manifest_verify_rc: int
    owner_fix_manifest_verify_rc: int
    parent_execution_manifest_verify_rc: int


@dataclass(frozen=True)
class ScopeExecutionResultV0:
    execution_scope: dict[str, Any]
    scope_definition: dict[str, Any]
    path_activation_binding: dict[str, Any]
    candidate_results: tuple[CandidateExecutionResultV0, ...]
    candidate_verdicts: dict[str, EconomicExecutionVerdict]
    sparse_signal_metrics: dict[str, dict[str, Any]]
    fleet_verdict: EconomicExecutionVerdict
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


def verify_owner_fix_evidence_manifest_v0(
    *,
    durable_evidence_root: Path,
) -> tuple[int, str]:
    from scripts.ops import primary_evidence_retention_v0 as retention

    bundle_dir = durable_evidence_root / "implementation" / OWNER_FIX_EVIDENCE_BUNDLE_SUFFIX
    if not bundle_dir.is_dir():
        return 1, f"missing_owner_fix_bundle:{bundle_dir}"
    ok, msg = retention.verify_manifest_sha256(bundle_dir)
    return (0, msg or "ok") if ok else (1, msg or "manifest_invalid")


def verify_parent_execution_evidence_manifest_v0(
    *,
    durable_evidence_root: Path,
) -> tuple[int, str]:
    from scripts.ops import primary_evidence_retention_v0 as retention

    bundle_dir = durable_evidence_root / "implementation" / PARENT_EXECUTION_EVIDENCE_BUNDLE_SUFFIX
    if not bundle_dir.is_dir():
        return 1, f"missing_parent_execution_bundle:{bundle_dir}"
    ok, msg = retention.verify_manifest_sha256(bundle_dir)
    return (0, msg or "ok") if ok else (1, msg or "manifest_invalid")


def verify_activation_evidence_manifest_v0(
    *,
    durable_evidence_root: Path,
) -> tuple[int, str]:
    from scripts.ops import primary_evidence_retention_v0 as retention

    bundle_dir = durable_evidence_root / "implementation" / ACTIVATION_EVIDENCE_BUNDLE_SUFFIX
    if not bundle_dir.is_dir():
        return 1, f"missing_activation_bundle:{bundle_dir}"
    ok, msg = retention.verify_manifest_sha256(bundle_dir)
    return (0, msg or "ok") if ok else (1, msg or "manifest_invalid")


def classify_candidate_verdict_v0(
    result: CandidateExecutionResultV0,
    *,
    evidence_payload: Mapping[str, Any],
) -> EconomicExecutionVerdict:
    if not result.runner_execution_success:
        return EconomicExecutionVerdict.EXECUTION_FAILED_FAIL_CLOSED
    trade_count = _metric_value(evidence_payload, "trade_count")
    net_return = _metric_value(evidence_payload, "net_return")
    metrics_present = any(value is not None for value in (trade_count, net_return))
    if not metrics_present and not evidence_payload:
        return EconomicExecutionVerdict.METRICS_NOT_MATERIALIZED
    if result.terminal_status is CandidateTerminalStatus.INCONCLUSIVE:
        return EconomicExecutionVerdict.INCONCLUSIVE_INSUFFICIENT_EVIDENCE
    if result.evidence_status == EconomicExecutionVerdict.ECONOMICALLY_VIABLE_OFFLINE.value:
        return EconomicExecutionVerdict.ECONOMICALLY_VIABLE_OFFLINE
    if (
        result.evidence_status == EconomicExecutionVerdict.ROBUSTNESS_FAILED.value
        or result.terminal_status is CandidateTerminalStatus.FAIL
    ):
        return EconomicExecutionVerdict.ROBUSTNESS_FAILED
    if not metrics_present:
        return EconomicExecutionVerdict.METRICS_NOT_MATERIALIZED
    return EconomicExecutionVerdict.INCONCLUSIVE_INSUFFICIENT_EVIDENCE


def classify_fleet_verdict_v0(
    candidate_verdicts: Sequence[EconomicExecutionVerdict],
) -> EconomicExecutionVerdict:
    if any(v is EconomicExecutionVerdict.EXECUTION_FAILED_FAIL_CLOSED for v in candidate_verdicts):
        return EconomicExecutionVerdict.EXECUTION_FAILED_FAIL_CLOSED
    if all(v is EconomicExecutionVerdict.METRICS_NOT_MATERIALIZED for v in candidate_verdicts):
        return EconomicExecutionVerdict.METRICS_NOT_MATERIALIZED
    if any(v is EconomicExecutionVerdict.METRICS_NOT_MATERIALIZED for v in candidate_verdicts):
        return EconomicExecutionVerdict.INCONCLUSIVE_INSUFFICIENT_EVIDENCE
    if any(
        v is EconomicExecutionVerdict.INCONCLUSIVE_INSUFFICIENT_EVIDENCE for v in candidate_verdicts
    ):
        return EconomicExecutionVerdict.INCONCLUSIVE_INSUFFICIENT_EVIDENCE
    if all(v is EconomicExecutionVerdict.ECONOMICALLY_VIABLE_OFFLINE for v in candidate_verdicts):
        return EconomicExecutionVerdict.ECONOMICALLY_VIABLE_OFFLINE
    return EconomicExecutionVerdict.ROBUSTNESS_FAILED


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


def verify_scope_definition_v0(scope_definition: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if scope_definition.get("status") != "SCOPE_DEFINED_NOT_EXECUTED":
        reasons.append(REASON_SCOPE_DEFINITION_STATUS_INVALID)
    if str(scope_definition.get("required_next_go_for_execution", "")) != CONFIRM_GO:
        reasons.append(REASON_SCOPE_DEFINITION_NEXT_GO_MISMATCH)
    return not reasons, tuple(reasons)


def verify_execution_scope_v0(
    scope: Mapping[str, Any],
    *,
    path_activation_binding: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if scope.get("binding_ready") is not True:
        reasons.append(REASON_SCOPE_BINDING_NOT_READY)
    if str(scope.get("scope_digest", "")) != EXECUTION_SCOPE_DIGEST:
        reasons.append(REASON_SCOPE_DIGEST_MISMATCH)
    if str(scope.get("semantic_digest", "")) != EXECUTION_SEMANTIC_DIGEST:
        reasons.append(REASON_SEMANTIC_DIGEST_MISMATCH)
    if str(scope.get("binding_completion_digest", "")) != PATH_ACTIVATION_BINDING_COMPLETION_DIGEST:
        reasons.append(REASON_COMPLETION_DIGEST_MISMATCH)
    if str(scope.get("evidence_class_id", "")) != EVIDENCE_CLASS_ID:
        reasons.append(REASON_EVIDENCE_CLASS_MISMATCH)
    if str(scope.get("execution_go_token", "")) != CONFIRM_GO:
        reasons.append("EXECUTION_CONFIRM_GO_MISMATCH")
    if scope.get("retry_unchanged_binding_allowed") is not False:
        reasons.append("RETRY_UNCHANGED_BINDING_MUST_BE_FALSE")
    if scope.get("path_activation_binding_ratified") is not True:
        reasons.append(REASON_PATH_ACTIVATION_NOT_RATIFIED)
    if str(scope.get("metric_materialization_path_ref", "")) != METRIC_MATERIALIZATION_PATH_REF:
        reasons.append("METRIC_MATERIALIZATION_PATH_REF_MISMATCH")
    completion_digest = str(path_activation_binding.get("completion_digest", ""))
    if completion_digest != PATH_ACTIVATION_BINDING_COMPLETION_DIGEST:
        reasons.append(f"{REASON_COMPLETION_DIGEST_MISMATCH}:{completion_digest}")
    if scope.get("step31f_owner_fix_applied") is not True:
        reasons.append("STEP31F_OWNER_FIX_NOT_APPLIED")
    if str(scope.get("owner_fix_module_ref", "")) != OWNER_FIX_MODULE_REF:
        reasons.append("OWNER_FIX_MODULE_REF_MISMATCH")
    retry_ok, retry_reasons = verify_unmodified_retry_admissibility_v0(
        fleet_binding_completion=path_activation_binding,
        requested_execution_evidence_class=EVIDENCE_CLASS_ID,
    )
    if not retry_ok:
        reasons.extend(retry_reasons)
    return not reasons, tuple(reasons)


def verify_execution_start_state_v0(
    *,
    repo_root: Path,
    durable_evidence_root: Path | None = None,
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
    scope_definition_path = repo_root / SCOPE_DEFINITION_REL
    binding_path = repo_root / PATH_ACTIVATION_BINDING_REL

    for missing_path, code in (
        (scope_path, REASON_EXECUTION_SCOPE_CONFIG_MISSING),
        (scope_definition_path, REASON_SCOPE_DEFINITION_MISSING),
        (binding_path, "PATH_ACTIVATION_BINDING_COMPLETION_MISSING"),
    ):
        if not missing_path.is_file():
            reasons.append(code)

    execution_scope: dict[str, Any] = {}
    scope_definition: dict[str, Any] = {}
    path_activation_binding: dict[str, Any] = {}
    if scope_path.is_file():
        execution_scope = _load_json(scope_path)
    if scope_definition_path.is_file():
        scope_definition = _load_json(scope_definition_path)
    if binding_path.is_file():
        path_activation_binding = _load_json(binding_path)

    activation_manifest_rc = 0
    owner_fix_manifest_rc = 0
    parent_execution_manifest_rc = 0
    if durable_evidence_root is not None:
        activation_manifest_rc, activation_msg = verify_activation_evidence_manifest_v0(
            durable_evidence_root=durable_evidence_root,
        )
        if activation_manifest_rc != 0:
            reasons.append(f"{REASON_ACTIVATION_MANIFEST_INVALID}:{activation_msg}")
        owner_fix_manifest_rc, owner_fix_msg = verify_owner_fix_evidence_manifest_v0(
            durable_evidence_root=durable_evidence_root,
        )
        if owner_fix_manifest_rc != 0:
            reasons.append(f"{REASON_OWNER_FIX_MANIFEST_INVALID}:{owner_fix_msg}")
        parent_execution_manifest_rc, parent_msg = verify_parent_execution_evidence_manifest_v0(
            durable_evidence_root=durable_evidence_root,
        )
        if parent_execution_manifest_rc != 0:
            reasons.append(f"{REASON_PARENT_EXECUTION_MANIFEST_INVALID}:{parent_msg}")

    if path_activation_binding.get("status") != (
        "PATH_ACTIVATION_BINDING_RATIFICATION_COMPLETE_NOT_EXECUTED"
    ):
        reasons.append(REASON_BINDING_STATUS_INVALID)
    if path_activation_binding.get("path_activation_binding_ratified") is not True:
        reasons.append(REASON_PATH_ACTIVATION_NOT_RATIFIED)
    if path_activation_binding.get("economic_evaluation_executed") is not False:
        reasons.append(REASON_EVALUATION_ALREADY_EXECUTED)

    if scope_definition:
        definition_ok, definition_reasons = verify_scope_definition_v0(scope_definition)
        if not definition_ok:
            reasons.extend(definition_reasons)

    if execution_scope.get("execution_performed") is True:
        reasons.append(REASON_EVALUATION_ALREADY_EXECUTED)

    if execution_scope and path_activation_binding:
        scope_ok, scope_reasons = verify_execution_scope_v0(
            execution_scope,
            path_activation_binding=path_activation_binding,
        )
        if not scope_ok:
            reasons.extend(scope_reasons)

    if path_activation_binding:
        sparse_v2_path = repo_root / SPARSE_V2_BINDING_REL
        sparse_v2_completion: dict[str, Any] | None = None
        if sparse_v2_path.is_file():
            sparse_v2_completion = _load_json(sparse_v2_path)
        validation = (
            validate_post_no_pass_metric_materialization_path_activation_binding_ratification_v0(
                path_activation_binding,
                sparse_v2_completion=sparse_v2_completion,
            )
        )
        if validation.verdict != PathActivationValidationVerdict.ACCEPTED:
            reasons.extend(validation.fail_reasons)

    staging_root = resolve_panel_staging_root()
    if not staging_root.is_dir():
        reasons.append("PANEL_STAGING_ROOT_MISSING")

    return StartStateVerificationResultV0(
        valid=not reasons,
        fail_reasons=tuple(reasons),
        origin_main_sha=origin_main,
        execution_scope=execution_scope,
        scope_definition=scope_definition,
        path_activation_binding=path_activation_binding,
        activation_manifest_verify_rc=activation_manifest_rc,
        owner_fix_manifest_verify_rc=owner_fix_manifest_rc,
        parent_execution_manifest_verify_rc=parent_execution_manifest_rc,
    )


def materialize_candidate_evidence_record_v0(
    *,
    strategy_id: str,
    candidate_dir: Path,
    result: CandidateExecutionResultV0,
    candidate_binding: Mapping[str, Any],
    verdict: EconomicExecutionVerdict,
    sparse_metrics: Mapping[str, Any],
    evidence_payload: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "strategy_id": strategy_id,
        "strategy_version": STRATEGY_VERSION,
        "canonical_candidate_identifier": result.canonical_candidate_identifier,
        "status": verdict.value,
        "primary_cause": PRIMARY_CAUSE,
        "sparse_signal_density_metrics": dict(sparse_metrics),
        "reason_codes": list(result.reason_codes),
        "trade_count": _metric_value(evidence_payload, "trade_count"),
        "gross_return": _metric_value(evidence_payload, "gross_return"),
        "net_return": _metric_value(evidence_payload, "net_return"),
        "net_expectancy": _metric_value(evidence_payload, "net_expectancy"),
        "profit_factor": _metric_value(evidence_payload, "profit_factor"),
        "sharpe": _metric_value(evidence_payload, "sharpe"),
        "max_drawdown": _metric_value(evidence_payload, "max_drawdown"),
        "fee_drag": _metric_value(evidence_payload, "fee_drag"),
        "slippage_impact": _metric_value(evidence_payload, "slippage_impact"),
        "funding_drag": _metric_value(evidence_payload, "funding_drag"),
        "walk_forward_results": evidence_payload.get("walk_forward_results"),
        "monte_carlo_results": evidence_payload.get("monte_carlo_results"),
        "stress_results": evidence_payload.get("stress_results"),
        "evidence_status": evidence_payload.get("status"),
        "metrics_materialized": bool(evidence_payload),
        "manifest_verify_rc": result.manifest_verify_rc,
        "output_dir": str(candidate_dir),
        "run_id": result.run_id,
        "metric_materialization_path_ref": candidate_binding.get("metric_materialization_path_ref"),
        "input_bindings": {
            "strategy_binding": {
                "strategy_id": strategy_id,
                "strategy_version": STRATEGY_VERSION,
                "parameter_binding": candidate_binding.get("parameter_binding"),
                "implementation_digest": candidate_binding.get("implementation_digest"),
                "config_digest": candidate_binding.get("config_digest"),
            },
            "dataset_binding": candidate_binding.get("dataset_binding"),
            "period_binding": candidate_binding.get("period_binding"),
            "instrument_binding": candidate_binding.get("instrument_binding"),
        },
    }


def _write_brief_evidence_artifacts_v0(
    *,
    evidence_root: Path,
    start_state: StartStateVerificationResultV0,
    candidate_records: Mapping[str, Mapping[str, Any]],
    candidate_verdicts: Mapping[str, EconomicExecutionVerdict],
    fleet_verdict: EconomicExecutionVerdict,
    fleet_status: FleetTerminalStatus,
    gate_pass: bool,
    commands: Sequence[str],
) -> None:
    metric_results = {
        "primary_cause": PRIMARY_CAUSE,
        "metric_materialization_path_ref": METRIC_MATERIALIZATION_PATH_REF,
        "fleet_verdict": fleet_verdict.value,
        "fleet_status": fleet_status.value,
        "economic_validity_offline_gate_pass": gate_pass,
        "candidate_verdicts": {sid: verdict.value for sid, verdict in candidate_verdicts.items()},
        "candidate_records": dict(candidate_records),
    }
    (evidence_root / "METRIC_MATERIALIZATION_RESULTS.json").write_text(
        json.dumps(metric_results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "ECONOMIC_EVALUATION_CLASSIFICATION.md").write_text(
        "\n".join(
            [
                "# Economic Evaluation Classification",
                "",
                f"- fleet_verdict: `{fleet_verdict.value}`",
                f"- fleet_status: `{fleet_status.value}`",
                f"- economic_validity_offline_gate_pass: `{gate_pass}`",
                f"- primary_cause: `{PRIMARY_CAUSE}`",
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
    (evidence_root / "BINDING_VERIFICATION.md").write_text(
        "\n".join(
            [
                "# Binding Verification",
                "",
                f"- path_activation_binding_ref: `{PATH_ACTIVATION_BINDING_REL}`",
                f"- binding_completion_digest: `{PATH_ACTIVATION_BINDING_COMPLETION_DIGEST}`",
                f"- execution_scope_ref: `{EXECUTION_SCOPE_REL}`",
                f"- scope_definition_ref: `{SCOPE_DEFINITION_REL}`",
                f"- activation_evidence_manifest_verify_rc: `{start_state.activation_manifest_verify_rc}`",
                f"- origin_main_sha: `{start_state.origin_main_sha}`",
                f"- path_activation_binding_ratified: `true`",
                f"- strategy_version: `{STRATEGY_VERSION}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_root / "SAFETY_BOUNDARY_CONFIRMATION.md").write_text(
        "\n".join(
            [
                "# Safety Boundary Confirmation",
                "",
                "- NO_LIVE=true",
                "- NO_RUNTIME=true",
                "- NO_SCHEDULER=true",
                "- NO_SHADOW=true",
                "- NO_PAPER=true",
                "- NO_TESTNET=true",
                "- NO_ORDERS=true",
                "- NO_ADAPTER_SUBMISSION=true",
                "- NO_CREDENTIALS=true",
                "- NO_ARMING=true",
                "- NO_RUNTIME_REWIRE=true",
                "- PROMOTION_ELIGIBLE=false",
                "- RUNTIME_REWIRE_ADMISSIBLE=false",
                "- authority_effect=NONE",
                "- runtime_effect=NONE",
                "- order_effect=NONE",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_root / "COMMANDS.log").write_text("\n".join(commands) + "\n", encoding="utf-8")
    (evidence_root / "COMMAND_LOG.md").write_text(
        "\n".join(["# Command Log", ""] + [f"- `{line}`" for line in commands]) + "\n",
        encoding="utf-8",
    )


def _write_environment_snapshot_v0(*, evidence_root: Path, repo_root: Path) -> None:
    import platform
    import sys

    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    head = result.stdout.strip() if result.returncode == 0 else "unknown"
    (evidence_root / "ENVIRONMENT_SNAPSHOT.md").write_text(
        "\n".join(
            [
                "# Environment Snapshot",
                "",
                f"- python_version: `{sys.version.split()[0]}`",
                f"- platform: `{platform.platform()}`",
                f"- repo_root: `{repo_root}`",
                f"- git_head: `{head}`",
                f"- origin_main_expected: `{EXPECTED_ORIGIN_MAIN_SHA}`",
                f"- owner_fix_module_ref: `{OWNER_FIX_MODULE_REF}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_required_closeout_artifacts_v0(
    *,
    evidence_root: Path,
    start_state: StartStateVerificationResultV0,
    candidate_records: Mapping[str, Mapping[str, Any]],
    candidate_verdicts: Mapping[str, EconomicExecutionVerdict],
    promotion_records: Mapping[str, Mapping[str, Any]],
    fleet_verdict: EconomicExecutionVerdict,
    fleet_status: FleetTerminalStatus,
    gate_pass: bool,
) -> None:
    result_classification = (
        "PASS"
        if gate_pass
        else (
            "INCONCLUSIVE"
            if fleet_verdict
            in (
                EconomicExecutionVerdict.INCONCLUSIVE_INSUFFICIENT_EVIDENCE,
                EconomicExecutionVerdict.EXECUTION_FAILED_FAIL_CLOSED,
                EconomicExecutionVerdict.METRICS_NOT_MATERIALIZED,
            )
            else "FAIL"
        )
    )
    (evidence_root / "ECONOMIC_EVALUATION_RESULT.md").write_text(
        "\n".join(
            [
                "# Economic Evaluation Result",
                "",
                f"- evidence_class_id: `{EVIDENCE_CLASS_ID}`",
                f"- fleet_verdict: `{fleet_verdict.value}`",
                f"- fleet_status: `{fleet_status.value}`",
                f"- economic_validity_offline_gate_pass: `{gate_pass}`",
                f"- result_classification: `{result_classification}`",
                f"- step31f_owner_fix_applied: `true`",
                "",
                "## Candidate results",
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
    (evidence_root / "PROMOTION_METRIC_MATERIALIZATION_REPORT.md").write_text(
        "\n".join(
            [
                "# Promotion Metric Materialization Report",
                "",
                f"- owner_fix_module_ref: `{OWNER_FIX_MODULE_REF}`",
                f"- metric_materialization_path_ref: `{METRIC_MATERIALIZATION_PATH_REF}`",
                "",
                "## Candidate materialization",
                "",
                *[
                    (
                        f"- `{sid}`: materialized="
                        f"`{promotion_records[sid].get('promotion_metrics_materialized')}` "
                        f"contract="
                        f"`{promotion_records[sid].get('dataset_manifest_contract_verdict')}` "
                        f"reasons=`{promotion_records[sid].get('reason_codes')}`"
                    )
                    for sid in RESEARCH_CANDIDATES
                    if sid in promotion_records
                ],
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_root / "FAILURE_OR_PASS_CLASSIFICATION.md").write_text(
        "\n".join(
            [
                "# Failure Or Pass Classification",
                "",
                f"- result_classification: `{result_classification}`",
                f"- fleet_verdict: `{fleet_verdict.value}`",
                f"- fleet_status: `{fleet_status.value}`",
                f"- economic_validity_offline_gate_pass: `{gate_pass}`",
                f"- owner_fix_manifest_verify_rc: `{start_state.owner_fix_manifest_verify_rc}`",
                f"- parent_execution_manifest_verify_rc: `{start_state.parent_execution_manifest_verify_rc}`",
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
    (evidence_root / "promotion_metric_materialization_records.json").write_text(
        json.dumps(dict(promotion_records), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_bounded_scope_v0(
    *,
    confirm: str,
    repo_root: Path,
    durable_evidence_root: Path,
    require_clean_worktree: bool = True,
    commands: Sequence[str] | None = None,
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

    from datetime import datetime, timezone

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_root = (
        durable_evidence_root
        / DURABLE_EVIDENCE_SUBDIR
        / f"{DURABLE_EVIDENCE_BUNDLE_PREFIX}_{ts_slug}"
    )
    evidence_root.mkdir(parents=True, exist_ok=False)

    execution_scope = start_state.execution_scope
    scope_definition = start_state.scope_definition
    path_activation_binding = start_state.path_activation_binding
    staging_root = resolve_panel_staging_root()
    command_log = list(commands or ())

    for name, payload in (
        ("execution_scope_v0.json", execution_scope),
        ("scope_definition_v0.json", scope_definition),
        ("path_activation_binding_v0.json", path_activation_binding),
    ):
        (evidence_root / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    go_consumption = {
        "consumed_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "go_token": CONFIRM_GO,
        "go_token_consumed": True,
        "scope_classification": SCOPE_CLASSIFICATION,
        "evidence_class_id": EVIDENCE_CLASS_ID,
    }
    (evidence_root / "go_token_consumption.json").write_text(
        json.dumps(go_consumption, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "INPUT_BINDINGS.json").write_text(
        json.dumps(
            {
                "execution_scope_ref": EXECUTION_SCOPE_REL,
                "execution_scope_digest": execution_scope.get("scope_digest"),
                "execution_semantic_digest": execution_scope.get("semantic_digest"),
                "scope_definition_ref": SCOPE_DEFINITION_REL,
                "binding_completion_digest": PATH_ACTIVATION_BINDING_COMPLETION_DIGEST,
                "evidence_class_id": EVIDENCE_CLASS_ID,
                "origin_main_sha": start_state.origin_main_sha,
                "go_token_consumed": CONFIRM_GO,
                "activation_evidence_bundle_suffix": ACTIVATION_EVIDENCE_BUNDLE_SUFFIX,
                "activation_manifest_verify_rc": start_state.activation_manifest_verify_rc,
                "owner_fix_evidence_bundle_suffix": OWNER_FIX_EVIDENCE_BUNDLE_SUFFIX,
                "owner_fix_manifest_verify_rc": start_state.owner_fix_manifest_verify_rc,
                "parent_execution_evidence_bundle_suffix": PARENT_EXECUTION_EVIDENCE_BUNDLE_SUFFIX,
                "parent_execution_manifest_verify_rc": start_state.parent_execution_manifest_verify_rc,
                "owner_fix_module_ref": OWNER_FIX_MODULE_REF,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    candidate_bindings = {
        str(candidate["strategy_id"]): candidate
        for candidate in path_activation_binding.get("candidates", [])
        if isinstance(candidate, Mapping)
    }

    candidate_results: list[CandidateExecutionResultV0] = []
    candidate_records: dict[str, dict[str, Any]] = {}
    candidate_verdicts: dict[str, EconomicExecutionVerdict] = {}
    sparse_signal_metrics: dict[str, dict[str, Any]] = {}
    promotion_records: dict[str, dict[str, Any]] = {}
    scratch_root = evidence_root / "panel_signal_density_scan"

    for strategy_id in RESEARCH_CANDIDATES:
        metrics = compute_sparse_signal_density_metrics_v0(
            repo_root=repo_root,
            strategy_id=strategy_id,
            staging_root=staging_root,
            scratch_root=scratch_root / strategy_id,
        )
        sparse_signal_metrics[strategy_id] = metrics.to_dict()
        (evidence_root / f"sparse_signal_density_metrics_{strategy_id}.json").write_text(
            json.dumps(metrics.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

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
        dataset_manifest: dict[str, Any] = {}
        from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
            extract_dataset_paths_from_config,
        )

        _dataset_path, manifest_path = extract_dataset_paths_from_config(
            json.loads(config_path.read_text(encoding="utf-8"))
        )
        if manifest_path.is_file():
            dataset_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        promotion_record = (
            materialize_promotion_metric_materialization_record_from_sparse_signal_inputs_v0(
                strategy_id=strategy_id,
                strategy_version=STRATEGY_VERSION,
                sparse_signal_density_metrics=metrics.to_dict(),
                dataset_manifest=dataset_manifest,
                promotion_metrics_payload=evidence_payload if evidence_payload else None,
            )
        )
        promotion_records[strategy_id] = promotion_record.to_dict()
        record = materialize_candidate_evidence_record_v0(
            strategy_id=strategy_id,
            candidate_dir=candidate_dir,
            result=result,
            candidate_binding=binding,
            verdict=verdict,
            sparse_metrics=metrics.to_dict(),
            evidence_payload=evidence_payload,
        )
        candidate_records[strategy_id] = record
        (evidence_root / f"candidate_evidence_{strategy_id}.json").write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    fleet_status = resolve_fleet_terminal_status_v0(candidate_results)
    fleet_verdict = classify_fleet_verdict_v0(list(candidate_verdicts.values()))
    gate_pass = fleet_status is FleetTerminalStatus.PASS and all(
        candidate_verdicts[sid] is EconomicExecutionVerdict.ECONOMICALLY_VIABLE_OFFLINE
        for sid in RESEARCH_CANDIDATES
    )

    ratification_stub = {
        "operator_scope_ratification_ref": PATH_ACTIVATION_BINDING_REL,
        "ratification_digest": path_activation_binding.get("completion_digest"),
        "fleet_binding_digest": path_activation_binding.get("completion_digest"),
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
    fleet_summary["execution_scope_digest"] = execution_scope.get("scope_digest")
    fleet_summary["fleet_verdict"] = fleet_verdict.value
    fleet_summary["candidate_verdicts"] = {
        sid: verdict.value for sid, verdict in candidate_verdicts.items()
    }
    fleet_summary["sparse_signal_density_metrics"] = sparse_signal_metrics
    fleet_summary["candidate_evidence_records"] = candidate_records
    fleet_summary["primary_cause"] = PRIMARY_CAUSE
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
    (evidence_root / "FLEET_VERDICT.json").write_text(
        json.dumps(
            {
                "fleet_verdict": fleet_verdict.value,
                "fleet_status": fleet_status.value,
                "economic_validity_offline_gate_pass": gate_pass,
                "candidate_verdicts": {sid: v.value for sid, v in candidate_verdicts.items()},
                "primary_cause": PRIMARY_CAUSE,
                "authority_effect": AUTHORITY_EFFECT,
                "runtime_effect": RUNTIME_EFFECT,
                "order_effect": ORDER_EFFECT,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_root / "EXECUTION_REPORT.md").write_text(
        "\n".join(
            [
                "# Execution Report",
                "",
                f"- evidence_class_id: `{EVIDENCE_CLASS_ID}`",
                f"- process_classification: `{PROCESS_CLASSIFICATION}`",
                f"- go_token_consumed: `{CONFIRM_GO}`",
                f"- origin_main_sha: `{start_state.origin_main_sha}`",
                f"- fleet_verdict: `{fleet_verdict.value}`",
                f"- fleet_status: `{fleet_status.value}`",
                f"- economic_validity_offline_gate_pass: `{gate_pass}`",
                f"- primary_cause: `{PRIMARY_CAUSE}`",
                f"- metric_materialization_path_ref: `{METRIC_MATERIALIZATION_PATH_REF}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    _write_brief_evidence_artifacts_v0(
        evidence_root=evidence_root,
        start_state=start_state,
        candidate_records=candidate_records,
        candidate_verdicts=candidate_verdicts,
        fleet_verdict=fleet_verdict,
        fleet_status=fleet_status,
        gate_pass=gate_pass,
        commands=command_log,
    )
    _write_environment_snapshot_v0(evidence_root=evidence_root, repo_root=repo_root)
    _write_required_closeout_artifacts_v0(
        evidence_root=evidence_root,
        start_state=start_state,
        candidate_records=candidate_records,
        candidate_verdicts=candidate_verdicts,
        promotion_records=promotion_records,
        fleet_verdict=fleet_verdict,
        fleet_status=fleet_status,
        gate_pass=gate_pass,
    )

    from scripts.ops import primary_evidence_retention_v0 as retention

    manifest_rc, _msg = retention.finalize_durable_bundle_manifest(evidence_root)

    return ScopeExecutionResultV0(
        execution_scope=execution_scope,
        scope_definition=scope_definition,
        path_activation_binding=path_activation_binding,
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
    "PATH_ACTIVATION_BINDING_COMPLETION_DIGEST",
    "EXECUTION_SCOPE_DIGEST",
    "EXECUTION_SEMANTIC_DIGEST",
    "EVIDENCE_CLASS_ID",
    "EconomicExecutionVerdict",
    "verify_preconditions_v0",
    "verify_execution_scope_v0",
    "verify_execution_start_state_v0",
    "verify_owner_fix_evidence_manifest_v0",
    "verify_parent_execution_evidence_manifest_v0",
    "verify_activation_evidence_manifest_v0",
    "run_bounded_scope_v0",
    "ScopeExecutionResultV0",
]
