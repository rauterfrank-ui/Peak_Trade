"""Post-no-pass sparse signal zero trade offline economic evaluation execution v0.

Deterministic, fail-closed offline execution for
POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0 using
ratified sparse-signal v2 fleet bindings. Reuses canonical STEP31F owners and panel
sequential signal-density adapter. No runtime, order, or authority effect.
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
from src.research.versioned_final_fleet_bindings_offline_economic_evaluation_v0 import (
    _run_candidate_with_runtime_config_v0,
)
from src.research.final_research_fleet_versioned_binding_completion_v0 import (
    canonical_candidate_identifier,
)
from src.research.panel_sequential_signal_density_research_adapter_v0 import (
    build_sparse_signal_runtime_step31f_config_v0,
    compute_sparse_signal_density_metrics_v0,
    resolve_panel_staging_root,
)
from src.research.post_no_pass_sparse_signal_zero_trade_offline_economic_evaluation_scope_ratification_v0 import (
    validate_scope_ratification_for_execution_v0,
)
from src.research.post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0 import (
    CONFIG_REL_PATH as SPARSE_BINDING_COMPLETION_REL,
    RESEARCH_CANDIDATES,
    STRATEGY_VERSION,
    ValidationVerdict as BindingValidationVerdict,
    validate_post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0,
)

PACKAGE_MARKER = (
    "POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0=true"
)

SCHEMA_VERSION = "post_no_pass_sparse_signal_zero_trade_offline_economic_evaluation_execution.v0"
EXECUTION_ID = "post_no_pass_sparse_signal_zero_trade_offline_economic_evaluation_execution_v0"
CANONICAL_SERIALIZATION_VERSION = "research_sparse_signal_execution_canonical_json_v1"

CONFIRM_GO = "GO_POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
SCOPE_CLASSIFICATION = (
    "POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
)
EXPECTED_ORIGIN_MAIN_SHA = "4698b49739976cdc3270922a38fad4b044ae5d26"

EXECUTION_SCOPE_REL = (
    "config/research/"
    "post_no_pass_sparse_signal_zero_trade_offline_economic_evaluation_execution_scope_v0.json"
)
SCOPE_DEFINITION_REL = (
    "config/research/post_no_pass_robustness_failure_next_research_scope_definition_v0.json"
)
SCOPE_RATIFICATION_REL = (
    "config/research/"
    "post_no_pass_sparse_signal_zero_trade_offline_economic_evaluation_scope_ratification_v0.json"
)

SPARSE_BINDING_COMPLETION_DIGEST = (
    "5bce4b1d05016ce8667f281ee0ae0874d0c4a640eddb72ee957a04ee86907913"
)
EXECUTION_SCOPE_DIGEST = "e59fe72d99ce58401fa510e7c852857d35ffbf74e49197094a92d33d058f522f"
EXECUTION_SEMANTIC_DIGEST = "6618669ed8ccebdb64f85a96f74a29c9b8aca3f88f83f96b37859c9cc7c6ba29"
EVIDENCE_CLASS_ID = "POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"

DURABLE_EVIDENCE_SUBDIR = "implementation"
DURABLE_EVIDENCE_BUNDLE_PREFIX = (
    "post_no_pass_sparse_signal_zero_trade_offline_economic_evaluation_execution_v0"
)

DEFAULT_DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)

REASON_EXECUTION_SCOPE_CONFIG_MISSING = "EXECUTION_SCOPE_CONFIG_MISSING"
REASON_SCOPE_DEFINITION_MISSING = "SCOPE_DEFINITION_CONFIG_MISSING"
REASON_SCOPE_BINDING_NOT_READY = "EXECUTION_SCOPE_BINDING_NOT_READY"
REASON_SCOPE_DIGEST_MISMATCH = "EXECUTION_SCOPE_DIGEST_MISMATCH"
REASON_SEMANTIC_DIGEST_MISMATCH = "EXECUTION_SEMANTIC_DIGEST_MISMATCH"
REASON_EVIDENCE_CLASS_MISMATCH = "EVIDENCE_CLASS_ID_MISMATCH"
REASON_COMPLETION_DIGEST_MISMATCH = "BINDING_COMPLETION_DIGEST_MISMATCH"
REASON_SCOPE_RATIFICATION_MISSING = "OFFLINE_SCOPE_RATIFICATION_MISSING"
REASON_EVALUATION_ALREADY_EXECUTED = "ECONOMIC_EVALUATION_ALREADY_EXECUTED"
REASON_WORKTREE_DIRTY = "WORKTREE_NOT_CLEAN"
REASON_BINDING_STATUS_INVALID = "SPARSE_BINDING_STATUS_INVALID"


class EconomicExecutionVerdict(str, Enum):
    ECONOMICALLY_VIABLE_OFFLINE = "ECONOMICALLY_VIABLE_OFFLINE"
    ROBUSTNESS_FAILED = "ROBUSTNESS_FAILED"
    INCONCLUSIVE_INSUFFICIENT_EVIDENCE = "INCONCLUSIVE_INSUFFICIENT_EVIDENCE"
    EXECUTION_FAILED_FAIL_CLOSED = "EXECUTION_FAILED_FAIL_CLOSED"
    SPARSE_SIGNAL_ZERO_TRADE = "SPARSE_SIGNAL_ZERO_TRADE"


@dataclass(frozen=True)
class StartStateVerificationResultV0:
    valid: bool
    fail_reasons: tuple[str, ...]
    origin_main_sha: str
    execution_scope: dict[str, Any]
    scope_definition: dict[str, Any]
    sparse_binding_completion: dict[str, Any]
    scope_ratification: dict[str, Any]


@dataclass(frozen=True)
class ScopeExecutionResultV0:
    execution_scope: dict[str, Any]
    scope_definition: dict[str, Any]
    sparse_binding_completion: dict[str, Any]
    scope_ratification: dict[str, Any]
    candidate_results: tuple[CandidateExecutionResultV0, ...]
    candidate_verdicts: dict[str, EconomicExecutionVerdict]
    sparse_signal_metrics: dict[str, dict[str, Any]]
    fleet_verdict: EconomicExecutionVerdict
    fleet_status: FleetTerminalStatus
    economic_validity_offline_gate_pass: bool
    manifest_verify_rc: int
    evidence_root: Path


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


def classify_candidate_verdict_v0(
    result: CandidateExecutionResultV0,
    *,
    sparse_metrics: Mapping[str, Any],
) -> EconomicExecutionVerdict:
    if not result.runner_execution_success:
        return EconomicExecutionVerdict.EXECUTION_FAILED_FAIL_CLOSED
    if sparse_metrics.get("instruments_with_nonzero_trades", 0) == 0:
        return EconomicExecutionVerdict.SPARSE_SIGNAL_ZERO_TRADE
    if result.terminal_status is CandidateTerminalStatus.INCONCLUSIVE:
        return EconomicExecutionVerdict.INCONCLUSIVE_INSUFFICIENT_EVIDENCE
    if result.evidence_status == EconomicExecutionVerdict.ECONOMICALLY_VIABLE_OFFLINE.value:
        return EconomicExecutionVerdict.ECONOMICALLY_VIABLE_OFFLINE
    if (
        result.evidence_status == EconomicExecutionVerdict.ROBUSTNESS_FAILED.value
        or result.terminal_status is CandidateTerminalStatus.FAIL
    ):
        return EconomicExecutionVerdict.ROBUSTNESS_FAILED
    return EconomicExecutionVerdict.INCONCLUSIVE_INSUFFICIENT_EVIDENCE


def classify_fleet_verdict_v0(
    candidate_verdicts: Sequence[EconomicExecutionVerdict],
) -> EconomicExecutionVerdict:
    if any(v is EconomicExecutionVerdict.EXECUTION_FAILED_FAIL_CLOSED for v in candidate_verdicts):
        return EconomicExecutionVerdict.EXECUTION_FAILED_FAIL_CLOSED
    if all(v is EconomicExecutionVerdict.SPARSE_SIGNAL_ZERO_TRADE for v in candidate_verdicts):
        return EconomicExecutionVerdict.SPARSE_SIGNAL_ZERO_TRADE
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


def verify_execution_scope_v0(
    scope: Mapping[str, Any],
    *,
    sparse_binding_completion: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if scope.get("binding_ready") is not True:
        reasons.append(REASON_SCOPE_BINDING_NOT_READY)
    if str(scope.get("scope_digest", "")) != EXECUTION_SCOPE_DIGEST:
        reasons.append(REASON_SCOPE_DIGEST_MISMATCH)
    if str(scope.get("semantic_digest", "")) != EXECUTION_SEMANTIC_DIGEST:
        reasons.append(REASON_SEMANTIC_DIGEST_MISMATCH)
    if str(scope.get("binding_completion_digest", "")) != SPARSE_BINDING_COMPLETION_DIGEST:
        reasons.append(REASON_COMPLETION_DIGEST_MISMATCH)
    if str(scope.get("evidence_class_id", "")) != EVIDENCE_CLASS_ID:
        reasons.append(REASON_EVIDENCE_CLASS_MISMATCH)
    if str(scope.get("execution_go_token", "")) != CONFIRM_GO:
        reasons.append("EXECUTION_CONFIRM_GO_MISMATCH")
    if scope.get("retry_unchanged_binding_allowed") is not False:
        reasons.append("RETRY_UNCHANGED_BINDING_MUST_BE_FALSE")
    if str(scope.get("previous_completion_digest", "")) != SPARSE_BINDING_COMPLETION_DIGEST:
        reasons.append("PREVIOUS_COMPLETION_DIGEST_MISMATCH")
    completion_digest = str(sparse_binding_completion.get("completion_digest", ""))
    if completion_digest != SPARSE_BINDING_COMPLETION_DIGEST:
        reasons.append(f"{REASON_COMPLETION_DIGEST_MISMATCH}:{completion_digest}")
    retry_ok, retry_reasons = verify_unmodified_retry_admissibility_v0(
        fleet_binding_completion=sparse_binding_completion,
        requested_execution_evidence_class=EVIDENCE_CLASS_ID,
    )
    if not retry_ok:
        reasons.extend(retry_reasons)
    return not reasons, tuple(reasons)


def verify_execution_start_state_v0(
    *,
    repo_root: Path,
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
    binding_path = repo_root / SPARSE_BINDING_COMPLETION_REL
    ratification_path = repo_root / SCOPE_RATIFICATION_REL

    for missing_path, code in (
        (scope_path, REASON_EXECUTION_SCOPE_CONFIG_MISSING),
        (scope_definition_path, REASON_SCOPE_DEFINITION_MISSING),
        (binding_path, "SPARSE_BINDING_COMPLETION_MISSING"),
        (ratification_path, REASON_SCOPE_RATIFICATION_MISSING),
    ):
        if not missing_path.is_file():
            reasons.append(code)

    execution_scope: dict[str, Any] = {}
    scope_definition: dict[str, Any] = {}
    sparse_binding_completion: dict[str, Any] = {}
    scope_ratification: dict[str, Any] = {}
    if scope_path.is_file():
        execution_scope = _load_json(scope_path)
    if scope_definition_path.is_file():
        scope_definition = _load_json(scope_definition_path)
    if binding_path.is_file():
        sparse_binding_completion = _load_json(binding_path)
    if ratification_path.is_file():
        scope_ratification = _load_json(ratification_path)

    if sparse_binding_completion.get("status") != "BINDING_RATIFICATION_COMPLETE_NOT_EXECUTED":
        reasons.append(REASON_BINDING_STATUS_INVALID)
    if sparse_binding_completion.get("economic_evaluation_executed") is not False:
        reasons.append(REASON_EVALUATION_ALREADY_EXECUTED)

    if execution_scope and sparse_binding_completion:
        scope_ok, scope_reasons = verify_execution_scope_v0(
            execution_scope,
            sparse_binding_completion=sparse_binding_completion,
        )
        if not scope_ok:
            reasons.extend(scope_reasons)

    if sparse_binding_completion:
        binding_verdict = (
            validate_post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0(
                sparse_binding_completion
            )
        )
        if binding_verdict.verdict != BindingValidationVerdict.ACCEPTED:
            reasons.extend(binding_verdict.fail_reasons)

    if scope_ratification and sparse_binding_completion:
        rat_ok, rat_reasons = validate_scope_ratification_for_execution_v0(
            scope_ratification,
            sparse_binding_completion=sparse_binding_completion,
        )
        if not rat_ok:
            reasons.extend(rat_reasons)

    staging_root = resolve_panel_staging_root()
    if not staging_root.is_dir():
        reasons.append("PANEL_STAGING_ROOT_MISSING")

    return StartStateVerificationResultV0(
        valid=not reasons,
        fail_reasons=tuple(reasons),
        origin_main_sha=origin_main,
        execution_scope=execution_scope,
        scope_definition=scope_definition,
        sparse_binding_completion=sparse_binding_completion,
        scope_ratification=scope_ratification,
    )


def materialize_candidate_evidence_record_v0(
    *,
    strategy_id: str,
    candidate_dir: Path,
    result: CandidateExecutionResultV0,
    candidate_binding: Mapping[str, Any],
    verdict: EconomicExecutionVerdict,
    sparse_metrics: Mapping[str, Any],
) -> dict[str, Any]:
    evidence_payload: dict[str, Any] = {}
    if (candidate_dir / ARTIFACT_FILENAME).is_file():
        try:
            loaded = load_economic_viability_evidence_bundle_v1(candidate_dir)
            evidence_payload = loaded.evidence.to_dict()
        except EconomicViabilityEvidenceError:
            evidence_payload = {}

    return {
        "strategy_id": strategy_id,
        "strategy_version": STRATEGY_VERSION,
        "canonical_candidate_identifier": result.canonical_candidate_identifier,
        "status": verdict.value,
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
        "evidence_status": evidence_payload.get("status"),
        "manifest_verify_rc": result.manifest_verify_rc,
        "output_dir": str(candidate_dir),
        "run_id": result.run_id,
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
    sparse_binding_completion = start_state.sparse_binding_completion
    scope_ratification = start_state.scope_ratification
    staging_root = resolve_panel_staging_root()

    for name, payload in (
        ("execution_scope_v0.json", execution_scope),
        ("scope_definition_v0.json", scope_definition),
        ("sparse_binding_completion_v0.json", sparse_binding_completion),
        ("offline_scope_ratification_v0.json", scope_ratification),
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
                "binding_completion_digest": SPARSE_BINDING_COMPLETION_DIGEST,
                "evidence_class_id": EVIDENCE_CLASS_ID,
                "origin_main_sha": start_state.origin_main_sha,
                "go_token_consumed": CONFIRM_GO,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    candidate_bindings = {
        str(candidate["strategy_id"]): candidate
        for candidate in sparse_binding_completion.get("candidates", [])
        if isinstance(candidate, Mapping)
    }

    candidate_results: list[CandidateExecutionResultV0] = []
    candidate_records: dict[str, dict[str, Any]] = {}
    candidate_verdicts: dict[str, EconomicExecutionVerdict] = {}
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
        verdict = classify_candidate_verdict_v0(result, sparse_metrics=metrics.to_dict())
        candidate_verdicts[strategy_id] = verdict
        binding = candidate_bindings.get(strategy_id, {})
        record = materialize_candidate_evidence_record_v0(
            strategy_id=strategy_id,
            candidate_dir=candidate_dir,
            result=result,
            candidate_binding=binding,
            verdict=verdict,
            sparse_metrics=metrics.to_dict(),
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

    fleet_summary = materialize_fleet_evaluation_summary_v0(
        ratification=scope_ratification,
        candidate_results=candidate_results,
        execution_bundle_dir=str(evidence_root),
        origin_main_sha=start_state.origin_main_sha,
    )
    fleet_summary["scope_classification"] = SCOPE_CLASSIFICATION
    fleet_summary["go_token_consumed"] = CONFIRM_GO
    fleet_summary["evidence_class_id"] = EVIDENCE_CLASS_ID
    fleet_summary["execution_scope_digest"] = execution_scope.get("scope_digest")
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
    (evidence_root / "FLEET_VERDICT.json").write_text(
        json.dumps(
            {
                "fleet_verdict": fleet_verdict.value,
                "fleet_status": fleet_status.value,
                "economic_validity_offline_gate_pass": gate_pass,
                "candidate_verdicts": {sid: v.value for sid, v in candidate_verdicts.items()},
                "sparse_signal_class": fleet_verdict.value,
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
    (evidence_root / "AUTHORITY_BOUNDARY_STATEMENT.md").write_text(
        "\n".join(
            [
                "# Authority Boundary Statement",
                "",
                "- candidate_ratified=false",
                "- promotion_authorized=false",
                "- runtime_authority=false",
                "- orders_allowed=false",
                "- NO_RUNTIME / NO_ORDERS / NO_CREDENTIALS / NO_SCHEDULER",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    from scripts.ops import primary_evidence_retention_v0 as retention

    manifest_rc, _msg = retention.finalize_durable_bundle_manifest(evidence_root)

    return ScopeExecutionResultV0(
        execution_scope=execution_scope,
        scope_definition=scope_definition,
        sparse_binding_completion=sparse_binding_completion,
        scope_ratification=scope_ratification,
        candidate_results=tuple(candidate_results),
        candidate_verdicts=candidate_verdicts,
        sparse_signal_metrics=sparse_signal_metrics,
        fleet_verdict=fleet_verdict,
        fleet_status=fleet_status,
        economic_validity_offline_gate_pass=gate_pass,
        manifest_verify_rc=manifest_rc,
        evidence_root=evidence_root,
    )


__all__ = [
    "CONFIRM_GO",
    "SCOPE_CLASSIFICATION",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "SPARSE_BINDING_COMPLETION_DIGEST",
    "EXECUTION_SCOPE_DIGEST",
    "EXECUTION_SEMANTIC_DIGEST",
    "EVIDENCE_CLASS_ID",
    "EconomicExecutionVerdict",
    "verify_preconditions_v0",
    "verify_execution_scope_v0",
    "verify_execution_start_state_v0",
    "run_bounded_scope_v0",
    "ScopeExecutionResultV0",
]
