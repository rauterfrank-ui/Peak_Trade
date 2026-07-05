"""Bounded new evidence class offline economic evaluation execution v0.

Deterministic, fail-closed offline execution for FINAL_RESEARCH_FLEET_OKX_FULL_PANEL_NEW_EVIDENCE_CLASS_V0
using ratified OKX full-panel bindings from PR #4845. Reuses canonical STEP29M/STEP31F owners.
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
    HISTORICAL_STEP31F_BINDING_COMPLETION_DIGEST,
    ORDER_EFFECT,
    REASON_BINDING_DIGEST_MISMATCH,
    REASON_GO_TOKEN_INVALID,
    REASON_ORIGIN_MAIN_MISMATCH,
    REASON_UNMODIFIED_BINDING_RETRY_BLOCKED,
    RUNTIME_EFFECT,
    dumps_execution_canonical_v1,
    materialize_fleet_evaluation_summary_v0,
    resolve_fleet_terminal_status_v0,
    run_candidate_economic_evaluation_v0,
    verify_unmodified_retry_admissibility_v0,
)
from src.research.final_research_fleet_okx_full_panel_versioned_binding_and_offline_economic_evaluation_v0 import (
    STEP31F_OKX_FULL_PANEL_CONFIG_PATHS,
    ValidationVerdict,
    validate_binding_completion_v0,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    FLEET_CANDIDATES,
)
from src.research.final_research_fleet_versioned_binding_completion_v0 import (
    canonical_candidate_identifier,
)

PACKAGE_MARKER = "BOUNDED_NEW_EVIDENCE_CLASS_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0=true"

SCHEMA_VERSION = "bounded_new_evidence_class_offline_economic_evaluation_execution.v0"
EXECUTION_ID = "bounded_new_evidence_class_offline_economic_evaluation_execution_v0"
EXECUTION_VERSION = "v0"
CANONICAL_SERIALIZATION_VERSION = "research_new_evidence_class_execution_canonical_json_v1"

GO_TOKEN = "GO_BOUNDED_NEW_EVIDENCE_CLASS_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
SCOPE_CLASSIFICATION = "BOUNDED_NEW_EVIDENCE_CLASS_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
EXPECTED_ORIGIN_MAIN_SHA = "ab851bd6a9fa102208f834b998367bd2ab7416f7"

NEW_EVIDENCE_CLASS_SCOPE_REL = (
    "config/research/final_research_fleet_new_evidence_class_scope_v0.json"
)
BINDING_COMPLETION_REL = (
    "config/research/final_research_fleet_okx_full_panel_versioned_binding_completion_v0.json"
)
SCOPE_RATIFICATION_REL = "config/research/final_research_fleet_okx_full_panel_offline_economic_evaluation_scope_ratification_v0.json"

NEW_BINDING_COMPLETION_DIGEST = "c5e3b5fe6b688b49dbd2b210fd63bdea79201d64820591f87091b4e20689a9dd"
NEW_EVIDENCE_CLASS_SCOPE_DIGEST = "64da0eae56a70ad0661398db14d712f6d58d6ea9f6ad0dbb73f3de2b01d11d67"
NEW_EVIDENCE_CLASS_SEMANTIC_DIGEST = (
    "00dd4140c3302f6703203c5c02e46ff9351345d8c8a83ba1d9ca03e173656e96"
)
EVIDENCE_CLASS_ID = "FINAL_RESEARCH_FLEET_OKX_FULL_PANEL_NEW_EVIDENCE_CLASS_V0"

DURABLE_EVIDENCE_SUBDIR = "implementation"
DURABLE_EVIDENCE_BUNDLE_PREFIX = (
    "bounded_new_evidence_class_offline_economic_evaluation_execution_v0"
)

DEFAULT_DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
PR4845_CLOSEOUT_BUNDLE = (
    "implementation/final_research_fleet_new_evidence_class_scope_pr4845_squash_merge_closeout_v0_"
    "20260705T003158Z"
)

REASON_SCOPE_CONFIG_MISSING = "NEW_EVIDENCE_CLASS_SCOPE_CONFIG_MISSING"
REASON_SCOPE_BINDING_NOT_READY = "NEW_EVIDENCE_CLASS_BINDING_NOT_READY"
REASON_SCOPE_DIGEST_MISMATCH = "NEW_EVIDENCE_CLASS_SCOPE_DIGEST_MISMATCH"
REASON_SEMANTIC_DIGEST_MISMATCH = "NEW_EVIDENCE_CLASS_SEMANTIC_DIGEST_MISMATCH"
REASON_EVIDENCE_CLASS_MISMATCH = "NEW_EVIDENCE_CLASS_ID_MISMATCH"
REASON_COMPLETION_DIGEST_MISMATCH = "NEW_BINDING_COMPLETION_DIGEST_MISMATCH"
REASON_SCOPE_RATIFICATION_MISSING = "OFFLINE_SCOPE_RATIFICATION_MISSING"
REASON_EVALUATION_ALREADY_EXECUTED = "ECONOMIC_EVALUATION_ALREADY_EXECUTED"
REASON_WORKTREE_DIRTY = "WORKTREE_NOT_CLEAN"
REASON_START_STATE_INVALID = "START_STATE_INVALID"


class EconomicExecutionVerdict(str, Enum):
    ECONOMICALLY_VIABLE_OFFLINE = "ECONOMICALLY_VIABLE_OFFLINE"
    ROBUSTNESS_FAILED = "ROBUSTNESS_FAILED"
    INCONCLUSIVE_INSUFFICIENT_EVIDENCE = "INCONCLUSIVE_INSUFFICIENT_EVIDENCE"
    EXECUTION_FAILED_FAIL_CLOSED = "EXECUTION_FAILED_FAIL_CLOSED"


@dataclass(frozen=True)
class StartStateVerificationResultV0:
    valid: bool
    fail_reasons: tuple[str, ...]
    origin_main_sha: str
    new_evidence_class_scope: dict[str, Any]
    fleet_binding_completion: dict[str, Any]
    scope_ratification: dict[str, Any]


@dataclass(frozen=True)
class ScopeExecutionResultV0:
    new_evidence_class_scope: dict[str, Any]
    fleet_binding_completion: dict[str, Any]
    scope_ratification: dict[str, Any]
    candidate_results: tuple[CandidateExecutionResultV0, ...]
    candidate_verdicts: dict[str, EconomicExecutionVerdict]
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
) -> EconomicExecutionVerdict:
    if not result.runner_execution_success:
        return EconomicExecutionVerdict.EXECUTION_FAILED_FAIL_CLOSED
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
    if confirm != GO_TOKEN:
        reasons.append(REASON_GO_TOKEN_INVALID)
    resolved = origin_main_sha or _resolve_origin_main_sha(repo_root)
    if resolved != EXPECTED_ORIGIN_MAIN_SHA:
        reasons.append(f"{REASON_ORIGIN_MAIN_MISMATCH}:{resolved}")
    if require_clean_worktree and _worktree_dirty_count(repo_root) > 0:
        reasons.append(REASON_WORKTREE_DIRTY)
    return not reasons, tuple(reasons)


def verify_new_evidence_class_scope_v0(
    scope: Mapping[str, Any],
    *,
    fleet_binding_completion: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if scope.get("binding_ready") is not True:
        reasons.append(REASON_SCOPE_BINDING_NOT_READY)
    if str(scope.get("scope_digest", "")) != NEW_EVIDENCE_CLASS_SCOPE_DIGEST:
        reasons.append(REASON_SCOPE_DIGEST_MISMATCH)
    if str(scope.get("semantic_digest", "")) != NEW_EVIDENCE_CLASS_SEMANTIC_DIGEST:
        reasons.append(REASON_SEMANTIC_DIGEST_MISMATCH)
    if str(scope.get("new_binding_completion_digest", "")) != NEW_BINDING_COMPLETION_DIGEST:
        reasons.append(REASON_COMPLETION_DIGEST_MISMATCH)
    if str(scope.get("evidence_class_id", "")) != EVIDENCE_CLASS_ID:
        reasons.append(REASON_EVIDENCE_CLASS_MISMATCH)
    if scope.get("retry_unchanged_binding_allowed") is not False:
        reasons.append("RETRY_UNCHANGED_BINDING_MUST_BE_FALSE")
    if (
        str(scope.get("previous_completion_digest", ""))
        != HISTORICAL_STEP31F_BINDING_COMPLETION_DIGEST
    ):
        reasons.append("PREVIOUS_COMPLETION_DIGEST_MISMATCH")
    completion_digest = str(fleet_binding_completion.get("completion_digest", ""))
    if completion_digest != NEW_BINDING_COMPLETION_DIGEST:
        reasons.append(f"{REASON_COMPLETION_DIGEST_MISMATCH}:{completion_digest}")
    retry_ok, retry_reasons = verify_unmodified_retry_admissibility_v0(
        fleet_binding_completion=fleet_binding_completion,
        requested_execution_evidence_class=EVIDENCE_CLASS_ID,
    )
    if not retry_ok:
        reasons.extend(retry_reasons)
        if REASON_UNMODIFIED_BINDING_RETRY_BLOCKED in retry_reasons:
            pass
    return not reasons, tuple(reasons)


def verify_scope_ratification_v0(
    ratification: Mapping[str, Any],
    *,
    fleet_binding_completion: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if ratification.get("economic_evaluation_executed") is not False:
        reasons.append(REASON_EVALUATION_ALREADY_EXECUTED)
    if str(ratification.get("fleet_binding_digest", "")) != NEW_BINDING_COMPLETION_DIGEST:
        reasons.append(REASON_BINDING_DIGEST_MISMATCH)
    binding_digests = ratification.get("candidate_binding_digests")
    if isinstance(binding_digests, Mapping):
        for candidate in fleet_binding_completion.get("candidates", ()):
            if not isinstance(candidate, Mapping):
                continue
            ref = canonical_candidate_identifier(
                str(candidate["strategy_id"]), str(candidate["strategy_version"])
            )
            expected = str(candidate.get("binding_semantic_digest", ""))
            actual = binding_digests.get(ref)
            if actual != expected:
                reasons.append(f"{REASON_BINDING_DIGEST_MISMATCH}:{ref}")
    for effect_field, expected in (
        ("authority_effect", AUTHORITY_EFFECT),
        ("runtime_effect", RUNTIME_EFFECT),
        ("order_effect", ORDER_EFFECT),
    ):
        if ratification.get(effect_field) != expected:
            reasons.append(f"EFFECT_NOT_NONE:{effect_field}")
    if ratification.get("runtime_rewire_admissible") is not False:
        reasons.append("RUNTIME_REWIRE_MUST_BE_FALSE")
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
        confirm=GO_TOKEN,
        origin_main_sha=origin_main,
        require_clean_worktree=require_clean_worktree,
    )
    if not pre_ok:
        reasons.extend(pre_reasons)

    scope_path = repo_root / NEW_EVIDENCE_CLASS_SCOPE_REL
    binding_path = repo_root / BINDING_COMPLETION_REL
    ratification_path = repo_root / SCOPE_RATIFICATION_REL
    if not scope_path.is_file():
        reasons.append(REASON_SCOPE_CONFIG_MISSING)
    if not binding_path.is_file():
        reasons.append("BINDING_COMPLETION_MISSING")
    if not ratification_path.is_file():
        reasons.append(REASON_SCOPE_RATIFICATION_MISSING)

    scope: dict[str, Any] = {}
    fleet_binding_completion: dict[str, Any] = {}
    scope_ratification: dict[str, Any] = {}
    if scope_path.is_file():
        scope = _load_json(scope_path)
    if binding_path.is_file():
        fleet_binding_completion = _load_json(binding_path)
    if ratification_path.is_file():
        scope_ratification = _load_json(ratification_path)

    if scope and fleet_binding_completion:
        scope_ok, scope_reasons = verify_new_evidence_class_scope_v0(
            scope,
            fleet_binding_completion=fleet_binding_completion,
        )
        if not scope_ok:
            reasons.extend(scope_reasons)

    if fleet_binding_completion:
        binding_validation = validate_binding_completion_v0(
            fleet_binding_completion,
            repo_root=repo_root,
        )
        if binding_validation.verdict is not ValidationVerdict.ACCEPTED:
            reasons.extend(binding_validation.fail_reasons)

    if scope_ratification and fleet_binding_completion:
        rat_ok, rat_reasons = verify_scope_ratification_v0(
            scope_ratification,
            fleet_binding_completion=fleet_binding_completion,
        )
        if not rat_ok:
            reasons.extend(rat_reasons)

    return StartStateVerificationResultV0(
        valid=not reasons,
        fail_reasons=tuple(reasons),
        origin_main_sha=origin_main,
        new_evidence_class_scope=scope,
        fleet_binding_completion=fleet_binding_completion,
        scope_ratification=scope_ratification,
    )


def materialize_candidate_evidence_record_v0(
    *,
    strategy_id: str,
    candidate_dir: Path,
    result: CandidateExecutionResultV0,
    candidate_binding: Mapping[str, Any],
    verdict: EconomicExecutionVerdict,
) -> dict[str, Any]:
    evidence_payload: dict[str, Any] = {}
    reason_codes: list[str] = list(result.reason_codes)
    validity_path = candidate_dir / "economic_validity_evaluation_v1.json"
    if validity_path.is_file():
        validity = _load_json(validity_path)
        raw_codes = validity.get("reason_codes")
        if isinstance(raw_codes, list):
            reason_codes = [str(code) for code in raw_codes]

    if (candidate_dir / ARTIFACT_FILENAME).is_file():
        try:
            loaded = load_economic_viability_evidence_bundle_v1(candidate_dir)
            evidence_payload = loaded.evidence.to_dict()
        except EconomicViabilityEvidenceError:
            evidence_payload = {}

    return {
        "strategy_id": strategy_id,
        "strategy_version": candidate_binding.get("strategy_version", "v1"),
        "canonical_candidate_identifier": result.canonical_candidate_identifier,
        "status": verdict.value,
        "reason_codes": reason_codes,
        "input_bindings": {
            "strategy_binding": {
                "strategy_id": strategy_id,
                "strategy_version": candidate_binding.get("strategy_version"),
                "parameter_binding": candidate_binding.get("parameter_binding"),
                "implementation_digest": candidate_binding.get("implementation_digest"),
                "config_digest": candidate_binding.get("config_digest"),
            },
            "dataset_binding": candidate_binding.get("dataset_binding"),
            "period_binding": candidate_binding.get("period_binding"),
            "instrument_binding": candidate_binding.get("instrument_binding"),
            "fee_model_binding": candidate_binding.get("fee_model_binding"),
            "slippage_model_binding": candidate_binding.get("slippage_model_binding"),
            "funding_model_binding": candidate_binding.get("funding_model_binding"),
            "execution_model_binding": candidate_binding.get("execution_model_binding"),
            "economic_policy_binding": candidate_binding.get("economic_policy_binding"),
        },
        "config_digest": evidence_payload.get("config_digest")
        or candidate_binding.get("config_digest"),
        "implementation_digest": evidence_payload.get("implementation_digest")
        or candidate_binding.get("implementation_digest"),
        "data_digest": evidence_payload.get("data_digest") or candidate_binding.get("data_digest"),
        "gross_return": _metric_value(evidence_payload, "gross_return"),
        "net_return": _metric_value(evidence_payload, "net_return"),
        "net_expectancy": _metric_value(evidence_payload, "net_expectancy"),
        "profit_factor": _metric_value(evidence_payload, "profit_factor"),
        "sharpe": _metric_value(evidence_payload, "sharpe"),
        "sortino": _metric_value(evidence_payload, "sortino"),
        "max_drawdown": _metric_value(evidence_payload, "max_drawdown"),
        "calmar": _metric_value(evidence_payload, "calmar"),
        "trade_count": _metric_value(evidence_payload, "trade_count"),
        "turnover": _metric_value(evidence_payload, "turnover"),
        "fee_drag": _metric_value(evidence_payload, "fee_drag"),
        "funding_drag": _metric_value(evidence_payload, "funding_drag"),
        "slippage_impact": _metric_value(evidence_payload, "slippage_impact"),
        "tail_loss": _metric_value(evidence_payload, "tail_loss"),
        "long_contribution": _metric_value(evidence_payload, "long_contribution"),
        "short_contribution": _metric_value(evidence_payload, "short_contribution"),
        "regime_breakdown": evidence_payload.get("regime_breakdown"),
        "walk_forward_results": evidence_payload.get("walk_forward_results"),
        "monte_carlo_results": evidence_payload.get("monte_carlo_results"),
        "stress_results": evidence_payload.get("stress_results"),
        "parameter_sensitivity_results": evidence_payload.get("parameter_sensitivity_results"),
        "evidence_status": evidence_payload.get("status"),
        "manifest_verify_rc": result.manifest_verify_rc,
        "output_dir": str(candidate_dir),
        "run_id": result.run_id,
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

    scope = start_state.new_evidence_class_scope
    fleet_binding_completion = start_state.fleet_binding_completion
    scope_ratification = start_state.scope_ratification

    (evidence_root / "new_evidence_class_scope_v0.json").write_text(
        json.dumps(scope, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "fleet_binding_completion_v0.json").write_text(
        json.dumps(fleet_binding_completion, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "offline_scope_ratification_v0.json").write_text(
        json.dumps(scope_ratification, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "INPUT_BINDINGS.json").write_text(
        json.dumps(
            {
                "new_evidence_class_scope_ref": NEW_EVIDENCE_CLASS_SCOPE_REL,
                "new_evidence_class_scope_digest": scope.get("scope_digest"),
                "new_evidence_class_semantic_digest": scope.get("semantic_digest"),
                "new_binding_completion_digest": NEW_BINDING_COMPLETION_DIGEST,
                "evidence_class_id": EVIDENCE_CLASS_ID,
                "pr4845_closeout_bundle": PR4845_CLOSEOUT_BUNDLE,
                "origin_main_sha": start_state.origin_main_sha,
                "go_token_consumed": GO_TOKEN,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    candidate_bindings = {
        str(c["strategy_id"]): c
        for c in fleet_binding_completion.get("candidates", [])
        if isinstance(c, Mapping)
    }

    candidate_results: list[CandidateExecutionResultV0] = []
    candidate_records: dict[str, dict[str, Any]] = {}
    candidate_verdicts: dict[str, EconomicExecutionVerdict] = {}

    for strategy_id, strategy_version in FLEET_CANDIDATES:
        config_rel = STEP31F_OKX_FULL_PANEL_CONFIG_PATHS[strategy_id]
        config_path = repo_root / config_rel
        candidate_dir = evidence_root / "candidates" / f"{strategy_id}_{strategy_version}"
        candidate_dir.parent.mkdir(parents=True, exist_ok=True)
        result = run_candidate_economic_evaluation_v0(
            repo_root=repo_root,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            config_path=config_path,
            output_dir=candidate_dir,
        )
        candidate_results.append(result)
        verdict = classify_candidate_verdict_v0(result)
        candidate_verdicts[strategy_id] = verdict
        binding = candidate_bindings.get(strategy_id, {})
        record = materialize_candidate_evidence_record_v0(
            strategy_id=strategy_id,
            candidate_dir=candidate_dir,
            result=result,
            candidate_binding=binding,
            verdict=verdict,
        )
        candidate_records[strategy_id] = record
        (evidence_root / f"candidate_evidence_{strategy_id}.json").write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    fleet_status = resolve_fleet_terminal_status_v0(candidate_results)
    fleet_verdict = classify_fleet_verdict_v0(list(candidate_verdicts.values()))
    gate_pass = fleet_status is FleetTerminalStatus.PASS and all(
        r.economic_validity_offline_gate_pass for r in candidate_results
    )

    fleet_summary = materialize_fleet_evaluation_summary_v0(
        ratification=scope_ratification,
        candidate_results=candidate_results,
        execution_bundle_dir=str(evidence_root),
        origin_main_sha=start_state.origin_main_sha,
    )
    fleet_summary["scope_classification"] = SCOPE_CLASSIFICATION
    fleet_summary["go_token_consumed"] = GO_TOKEN
    fleet_summary["evidence_class_id"] = EVIDENCE_CLASS_ID
    fleet_summary["new_evidence_class_scope_digest"] = scope.get("scope_digest")
    fleet_summary["fleet_verdict"] = fleet_verdict.value
    fleet_summary["candidate_verdicts"] = {
        sid: verdict.value for sid, verdict in candidate_verdicts.items()
    }
    fleet_summary["candidate_evidence_records"] = candidate_records
    fleet_summary["authority_matrix"] = {
        "candidate_ratified": False,
        "promotion_authorized": False,
        "runtime_authority": False,
        "shadow_authorized": False,
        "paper_authorized": False,
        "testnet_authorized": False,
        "orders_allowed": False,
    }
    fleet_summary["manifest_digest"] = _stable_digest(
        {k: v for k, v in fleet_summary.items() if k != "manifest_digest"}
    )

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
                "- shadow_authorized=false",
                "- paper_authorized=false",
                "- testnet_authorized=false",
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
        new_evidence_class_scope=scope,
        fleet_binding_completion=fleet_binding_completion,
        scope_ratification=scope_ratification,
        candidate_results=tuple(candidate_results),
        candidate_verdicts=candidate_verdicts,
        fleet_verdict=fleet_verdict,
        fleet_status=fleet_status,
        economic_validity_offline_gate_pass=gate_pass,
        manifest_verify_rc=manifest_rc,
        evidence_root=evidence_root,
    )


__all__ = [
    "GO_TOKEN",
    "SCOPE_CLASSIFICATION",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "NEW_BINDING_COMPLETION_DIGEST",
    "EVIDENCE_CLASS_ID",
    "EconomicExecutionVerdict",
    "verify_preconditions_v0",
    "verify_execution_start_state_v0",
    "run_bounded_scope_v0",
    "ScopeExecutionResultV0",
]
