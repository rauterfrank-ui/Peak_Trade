"""Post-PR4922 offline economic evaluation execution v0.

Deterministic, fail-closed offline execution for versioned research bindings
materialized by PR #4922 (post-PR4921). Reuses canonical STEP31F owners,
panel narrow-dataset adapter, and economic viability evidence runner.
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
from src.research.bounded_offline_funding_fetch_for_materialized_panel_v0 import (
    FundingCoverageReportV0,
    PanelMemberBindingV0,
    compute_funding_coverage_report_v0,
    load_panel_member_binding_v0,
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
    NarrowDatasetMaterializationV0,
    _load_period_policy,
    _run_candidate_with_runtime_config_v0,
    materialize_narrow_evaluation_dataset_v0,
)

PACKAGE_MARKER = "POST_PR4922_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0=true"

SCHEMA_VERSION = "post_pr4922_offline_economic_evaluation_execution.v0"
EXECUTION_ID = "post_pr4922_offline_economic_evaluation_execution_v0"
CANONICAL_SERIALIZATION_VERSION = "research_post_pr4922_execution_canonical_json_v1"

CONFIRM_GO = "GO_POST_PR4922_VERSIONED_RESEARCH_BINDINGS_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
SCOPE_CLASSIFICATION = "OFFLINE_ECONOMIC_EVALUATION_EXECUTION_ONLY_NO_RUNTIME_AUTHORITY_V0"
PROCESS_CLASSIFICATION = "POST_PR4922_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
EVIDENCE_CLASS_ID = PROCESS_CLASSIFICATION
STRATEGY_VERSION = "v2"
EXPECTED_ORIGIN_MAIN_SHA = "a5cb8edef3edff2c1213aef2130cd0700c3b89c3"

BINDING_CONFIG_REL = "config/research/post_pr4921_versioned_research_bindings_no_eval_v0.json"
EXECUTION_CONFIG_REL = "config/research/post_pr4922_offline_economic_evaluation_execution_v0.json"
GOVERNANCE_REL_PATH = "docs/governance/POST_PR4922_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0.md"

BINDING_CONFIG_DIGEST = "cfdb5d550eea4a8311981227750909c21ab1339692500bb968a92953468dcdd5"
EXECUTION_SCOPE_DIGEST = "478267f4ae19f8f0e98aabf6d3e409b57a4773a044690b4fd915370a311b8d1a"
EXECUTION_SEMANTIC_DIGEST = "066d766bfa96fbf2134fd60d37b05920200ebd6570df0350d008b19029006a56"

PARENT_CLOSEOUT_SUFFIX = (
    "post_pr4921_versioned_research_bindings_no_eval_merge_closeout_20260706T083055Z"
)

DURABLE_EVIDENCE_SUBDIR = "research"
DURABLE_EVIDENCE_BUNDLE_PREFIX = "post_pr4922_offline_economic_evaluation_execution"

DEFAULT_DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)

FLEET_CANDIDATES: tuple[str, ...] = ("trend_following", "bollinger_bands", "momentum_1h")
EXCLUDED_V1_BINDINGS: frozenset[str] = frozenset(
    {"trend_following/v1", "bollinger_bands/v1", "momentum_1h/v1"}
)

STEP31F_TEMPLATE_CONFIG_PATHS: dict[str, str] = {
    "trend_following": (
        "config/ops/step31f_okx_inst_eth_usdt_perp_trend_following_v1_economic_evaluation_v1.json"
    ),
    "bollinger_bands": (
        "config/ops/step31f_okx_inst_eth_usdt_perp_bollinger_bands_v1_economic_evaluation_v1.json"
    ),
    "momentum_1h": (
        "config/ops/step31f_okx_inst_eth_usdt_perp_momentum_1h_v1_economic_evaluation_v1.json"
    ),
}

BINDING_MATERIALIZATION_VERDICT = "BINDINGS_MATERIALIZED_NOT_EVALUATED"

REASON_EXECUTION_CONFIG_MISSING = "EXECUTION_CONFIG_MISSING"
REASON_BINDING_CONFIG_MISSING = "BINDING_CONFIG_MISSING"
REASON_SCOPE_BINDING_NOT_READY = "EXECUTION_SCOPE_BINDING_NOT_READY"
REASON_SCOPE_DIGEST_MISMATCH = "EXECUTION_SCOPE_DIGEST_MISMATCH"
REASON_SEMANTIC_DIGEST_MISMATCH = "EXECUTION_SEMANTIC_DIGEST_MISMATCH"
REASON_EVIDENCE_CLASS_MISMATCH = "EVIDENCE_CLASS_ID_MISMATCH"
REASON_BINDING_CONFIG_DIGEST_MISMATCH = "BINDING_CONFIG_DIGEST_MISMATCH"
REASON_EVALUATION_ALREADY_EXECUTED = "ECONOMIC_EVALUATION_ALREADY_EXECUTED"
REASON_WORKTREE_DIRTY = "WORKTREE_NOT_CLEAN"
REASON_BINDING_STATUS_INVALID = "POST_PR4921_BINDING_STATUS_INVALID"
REASON_PARENT_MANIFEST_INVALID = "PARENT_CLOSEOUT_MANIFEST_INVALID"
REASON_STAGING_MISSING = "STAGING_MISSING"
REASON_FUNDING_COVERAGE_INCOMPLETE = "FAIL_CLOSED_DATASET_OR_FUNDING_COVERAGE_INCOMPLETE"
REASON_EXCLUDED_V1_RETRY = "EXCLUDED_V1_BINDING_RETRY_FORBIDDEN"


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
    execution_config: dict[str, Any]
    binding_config: dict[str, Any]
    parent_manifest_verify_rc: int
    panel_binding: PanelMemberBindingV0 | None
    funding_coverage: FundingCoverageReportV0 | None


@dataclass(frozen=True)
class ScopeExecutionResultV0:
    execution_config: dict[str, Any]
    binding_config: dict[str, Any]
    candidate_results: tuple[CandidateExecutionResultV0, ...]
    candidate_verdicts: dict[str, CandidateEconomicVerdict]
    fleet_verdict: FleetEconomicVerdict
    fleet_status: FleetTerminalStatus
    economic_validity_offline_gate_pass: bool
    manifest_verify_rc: int
    evidence_root: Path
    process_classification: str


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_binding_config_digest_v0(binding_config: Mapping[str, Any]) -> str:
    body = {
        k: binding_config[k]
        for k in (
            "schema_version",
            "verdict",
            "scope_id",
            "process_classification",
            "scope_classification",
            "versioned_bindings",
            "shared_model_bindings",
            "excluded_failed_v1_bindings",
        )
        if k in binding_config
    }
    return _stable_digest(body)


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
        "binding_config_digest": scope_body.get("binding_config_digest"),
        "evidence_class_id": scope_body.get("evidence_class_id"),
        "execution_go_token": scope_body.get("execution_go_token"),
        "fleet_candidates": scope_body.get("fleet_candidates"),
        "parent_closeout_suffix": scope_body.get("parent_closeout_suffix"),
        "retry_unchanged_binding_allowed": scope_body.get("retry_unchanged_binding_allowed"),
        "scope_classification": scope_body.get("scope_classification"),
        "strategy_version": scope_body.get("strategy_version"),
    }
    return _stable_digest(scope_fields), _stable_digest(semantic_fields)


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


def _resolve_staging_root(binding_config: Mapping[str, Any]) -> Path:
    bindings = binding_config.get("versioned_bindings", [])
    if bindings and isinstance(bindings[0], Mapping):
        panel_root = bindings[0].get("dataset_binding", {}).get("panel_staging_root")
        if isinstance(panel_root, str) and panel_root.strip():
            return Path(panel_root).resolve()
    raise ValueError(REASON_STAGING_MISSING)


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


def verify_parent_closeout_manifest_v0(
    *,
    durable_evidence_root: Path,
) -> tuple[int, str]:
    from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256

    parent_dir = durable_evidence_root / "implementation" / PARENT_CLOSEOUT_SUFFIX
    ok, msg = verify_manifest_sha256(parent_dir)
    return (0 if ok else 1), msg or "ok"


def verify_panel_staging_v0(
    staging_root: Path,
) -> tuple[bool, tuple[str, ...], PanelMemberBindingV0 | None, FundingCoverageReportV0]:
    reasons: list[str] = []
    panel_binding: PanelMemberBindingV0 | None = None
    coverage = FundingCoverageReportV0(
        row_count_total=0,
        missing_funding_count=0,
        populated_funding_count=0,
        coverage_ratio=0.0,
        fetched_from_okx_public=None,
        instrument_count=0,
        manifest_verified=False,
    )
    if not staging_root.is_dir():
        reasons.append(REASON_STAGING_MISSING)
    else:
        try:
            panel_binding = load_panel_member_binding_v0(staging_root)
        except FileNotFoundError as exc:
            reasons.append(str(exc))
        coverage = compute_funding_coverage_report_v0(staging_root)
        if coverage.coverage_ratio < 1.0 or coverage.missing_funding_count > 0:
            reasons.append(REASON_FUNDING_COVERAGE_INCOMPLETE)
    return not reasons, tuple(reasons), panel_binding, coverage


def verify_execution_scope_v0(
    scope: Mapping[str, Any],
    *,
    binding_config: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if scope.get("binding_ready") is not True:
        reasons.append(REASON_SCOPE_BINDING_NOT_READY)
    if str(scope.get("scope_digest", "")) != EXECUTION_SCOPE_DIGEST:
        reasons.append(REASON_SCOPE_DIGEST_MISMATCH)
    if str(scope.get("semantic_digest", "")) != EXECUTION_SEMANTIC_DIGEST:
        reasons.append(REASON_SEMANTIC_DIGEST_MISMATCH)
    if str(scope.get("binding_config_digest", "")) != BINDING_CONFIG_DIGEST:
        reasons.append(REASON_BINDING_CONFIG_DIGEST_MISMATCH)
    if str(scope.get("evidence_class_id", "")) != EVIDENCE_CLASS_ID:
        reasons.append(REASON_EVIDENCE_CLASS_MISMATCH)
    if str(scope.get("execution_go_token", "")) != CONFIRM_GO:
        reasons.append("EXECUTION_CONFIRM_GO_MISMATCH")
    if scope.get("retry_unchanged_binding_allowed") is not False:
        reasons.append("RETRY_UNCHANGED_BINDING_MUST_BE_FALSE")
    if str(scope.get("parent_closeout_suffix", "")) != PARENT_CLOSEOUT_SUFFIX:
        reasons.append("PARENT_CLOSEOUT_SUFFIX_MISMATCH")
    if str(scope.get("binding_config_ref", "")) != BINDING_CONFIG_REL:
        reasons.append("BINDING_CONFIG_REF_MISMATCH")
    if binding_config.get("verdict") != BINDING_MATERIALIZATION_VERDICT:
        reasons.append(REASON_BINDING_STATUS_INVALID)
    if binding_config.get("economic_evaluation_authorized") is not False:
        reasons.append(REASON_EVALUATION_ALREADY_EXECUTED)
    retry_ok, retry_reasons = verify_unmodified_retry_admissibility_v0(
        fleet_binding_completion={"completion_digest": BINDING_CONFIG_DIGEST},
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

    exec_path = repo_root / EXECUTION_CONFIG_REL
    binding_path = repo_root / BINDING_CONFIG_REL
    if not exec_path.is_file():
        reasons.append(REASON_EXECUTION_CONFIG_MISSING)
    if not binding_path.is_file():
        reasons.append(REASON_BINDING_CONFIG_MISSING)

    execution_config: dict[str, Any] = {}
    binding_config: dict[str, Any] = {}
    if exec_path.is_file():
        execution_config = _load_json(exec_path)
    if binding_path.is_file():
        binding_config = _load_json(binding_path)

    parent_manifest_rc, parent_msg = verify_parent_closeout_manifest_v0(
        durable_evidence_root=durable_evidence_root,
    )
    if parent_manifest_rc != 0:
        reasons.append(f"{REASON_PARENT_MANIFEST_INVALID}:{parent_msg}")

    panel_binding: PanelMemberBindingV0 | None = None
    funding_coverage: FundingCoverageReportV0 | None = None
    if binding_config:
        staging_root = _resolve_staging_root(binding_config)
        panel_ok, panel_reasons, panel_binding, funding_coverage = verify_panel_staging_v0(
            staging_root
        )
        if not panel_ok:
            reasons.extend(panel_reasons)
        excluded = set(binding_config.get("excluded_failed_v1_bindings", []))
        if excluded != EXCLUDED_V1_BINDINGS:
            reasons.append("EXCLUDED_V1_BINDINGS_MISMATCH")
        for binding in binding_config.get("versioned_bindings", []):
            if not isinstance(binding, Mapping):
                continue
            if binding.get("candidate_version") != STRATEGY_VERSION:
                reasons.append(f"UNEXPECTED_CANDIDATE_VERSION:{binding.get('candidate_id')}")
            if binding.get("binding_status") != "MATERIALIZED_NOT_EVALUATED":
                reasons.append(REASON_BINDING_STATUS_INVALID)
            excl = binding.get("excluded_failed_v1_binding")
            if excl in EXCLUDED_V1_BINDINGS and binding.get("retry_authorized") is True:
                reasons.append(REASON_EXCLUDED_V1_RETRY)

    if execution_config.get("execution_performed") is True:
        reasons.append(REASON_EVALUATION_ALREADY_EXECUTED)

    if execution_config and binding_config:
        scope_ok, scope_reasons = verify_execution_scope_v0(
            execution_config,
            binding_config=binding_config,
        )
        if not scope_ok:
            reasons.extend(scope_reasons)

    return StartStateVerificationResultV0(
        valid=not reasons,
        fail_reasons=tuple(reasons),
        origin_main_sha=origin_main,
        execution_config=execution_config,
        binding_config=binding_config,
        parent_manifest_verify_rc=parent_manifest_rc,
        panel_binding=panel_binding,
        funding_coverage=funding_coverage,
    )


def build_post_pr4922_runtime_step31f_config_v0(
    *,
    repo_root: Path,
    strategy_id: str,
    narrow_dataset: NarrowDatasetMaterializationV0,
    versioned_binding: Mapping[str, Any],
    output_path: Path,
) -> Path:
    from src.research.versioned_final_fleet_bindings_offline_economic_evaluation_v0 import (
        CANONICAL_INSTRUMENT_ID,
        EVALUATION_NATIVE_INSTRUMENT_ID,
    )

    template_path = repo_root / STEP31F_TEMPLATE_CONFIG_PATHS[strategy_id]
    cfg = json.loads(template_path.read_text(encoding="utf-8"))
    binding = dict(cfg["real_admissible_futures_evaluation_binding_v1"])
    binding["dataset_path"] = str(narrow_dataset.bars_path)
    binding["dataset_manifest_path"] = str(narrow_dataset.manifest_path)
    binding["expected_dataset_digest"] = narrow_dataset.dataset_digest
    binding["expected_manifest_digest"] = narrow_dataset.manifest_digest
    binding["training_period"] = narrow_dataset.training_period
    binding["validation_period"] = narrow_dataset.validation_period
    binding["out_of_sample_period"] = narrow_dataset.out_of_sample_period
    binding["native_instrument_id"] = EVALUATION_NATIVE_INSTRUMENT_ID
    binding["canonical_instrument_id"] = CANONICAL_INSTRUMENT_ID
    cfg["real_admissible_futures_evaluation_binding_v1"] = binding

    fee_binding = versioned_binding.get("fee_model_binding", {})
    slip_binding = versioned_binding.get("slippage_model_binding", {})
    fee_bps = float(fee_binding.get("fee_bps", 10.0))
    slippage_bps = float(slip_binding.get("conservative_half_spread_bps", 5.0))

    backtest = cfg.setdefault("backtest", {})
    if isinstance(backtest, dict):
        backtest["fee_bps"] = fee_bps
        backtest["slippage_bps"] = slippage_bps
        econ_cost = backtest.setdefault("economic_research_execution_cost", {})
        if isinstance(econ_cost, dict):
            econ_cost["fee_bps"] = fee_bps
            econ_cost["slippage_bps"] = slippage_bps
            econ_cost["conservative_half_spread_bps"] = slippage_bps

    param_binding = versioned_binding.get("parameter_binding", {})
    param_values = param_binding.get("values", {})
    eval_block = cfg.setdefault("economic_evaluation_v1", {})
    if isinstance(eval_block, dict):
        eval_block["strategy_id"] = strategy_id
        eval_block["strategy_version"] = STRATEGY_VERSION
        if isinstance(param_values, Mapping) and param_values:
            eval_block["strategy_params"] = dict(param_values)
        wf = eval_block.setdefault("walk_forward", {})
        if isinstance(wf, dict):
            wf["train_bars"] = 1200
            wf["test_bars"] = 300
            wf["step_bars"] = 300

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(cfg, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def materialize_candidate_result_v0(
    *,
    strategy_id: str,
    candidate_dir: Path,
    result: CandidateExecutionResultV0,
    versioned_binding: Mapping[str, Any],
    verdict: CandidateEconomicVerdict,
    evidence_payload: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "candidate_id": strategy_id,
        "candidate_version": STRATEGY_VERSION,
        "canonical_candidate_identifier": result.canonical_candidate_identifier,
        "verdict": verdict.value,
        "reason_codes": list(result.reason_codes),
        "trade_count": _metric_value(evidence_payload, "trade_count"),
        "gross_return": _metric_value(evidence_payload, "gross_return"),
        "net_return": _metric_value(evidence_payload, "net_return"),
        "net_expectancy": _metric_value(evidence_payload, "net_expectancy"),
        "profit_factor": _metric_value(evidence_payload, "profit_factor"),
        "sharpe": _metric_value(evidence_payload, "sharpe"),
        "max_drawdown": _metric_value(evidence_payload, "max_drawdown"),
        "turnover": _metric_value(evidence_payload, "turnover"),
        "fee_drag": _metric_value(evidence_payload, "fee_drag"),
        "slippage_impact": _metric_value(evidence_payload, "slippage_impact"),
        "funding_drag": _metric_value(evidence_payload, "funding_drag"),
        "walk_forward_results": evidence_payload.get("walk_forward_results"),
        "monte_carlo_results": evidence_payload.get("monte_carlo_results"),
        "stress_results": evidence_payload.get("stress_results"),
        "parameter_sensitivity_results": evidence_payload.get("parameter_sensitivity_results"),
        "evidence_status": evidence_payload.get("status"),
        "manifest_verify_rc": result.manifest_verify_rc,
        "output_dir": str(candidate_dir),
        "run_id": result.run_id,
        "parameter_binding": versioned_binding.get("parameter_binding"),
        "dataset_binding": versioned_binding.get("dataset_binding"),
        "fee_model_binding": versioned_binding.get("fee_model_binding"),
        "slippage_model_binding": versioned_binding.get("slippage_model_binding"),
        "funding_model_binding": versioned_binding.get("funding_model_binding"),
        "excluded_failed_v1_binding": versioned_binding.get("excluded_failed_v1_binding"),
    }


def _build_authority_boundary() -> dict[str, Any]:
    return {
        "backtest_execution_authorized": True,
        "binding_materialization_only": False,
        "bitcoin_direction_allowed": False,
        "economic_evaluation_authorized": True,
        "futures_only": True,
        "live_authorized": False,
        "monte_carlo_execution_authorized": True,
        "offline_only": True,
        "orders_allowed": False,
        "parameter_optimization_authorized": False,
        "promotion_admissible": False,
        "retry_authorized": False,
        "runtime_authority": "NONE",
        "runtime_rewire_admissible": False,
        "scheduler_runtime_allowed": False,
        "shadow_authorized": False,
        "stress_execution_authorized": True,
        "testnet_authorized": False,
        "threshold_lowering_authorized": False,
        "walk_forward_execution_authorized": True,
    }


def _write_required_bundle_artifacts_v0(
    *,
    evidence_root: Path,
    start_state: StartStateVerificationResultV0,
    binding_config: Mapping[str, Any],
    candidate_records: Mapping[str, Mapping[str, Any]],
    candidate_verdicts: Mapping[str, CandidateEconomicVerdict],
    fleet_verdict: FleetEconomicVerdict,
    fleet_status: FleetTerminalStatus,
    gate_pass: bool,
) -> None:
    evidence_by_candidate: dict[str, Any] = {}
    for strategy_id in FLEET_CANDIDATES:
        record = candidate_records.get(strategy_id, {})
        candidate_dir = Path(str(record.get("output_dir", "")))
        evidence_src = candidate_dir / ARTIFACT_FILENAME
        if evidence_src.is_file():
            evidence_by_candidate[strategy_id] = json.loads(
                evidence_src.read_text(encoding="utf-8")
            )

    (evidence_root / "binding_config_snapshot.json").write_text(
        json.dumps(binding_config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "candidate_economic_viability_evidence.json").write_text(
        json.dumps(evidence_by_candidate, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "candidate_verdicts.json").write_text(
        json.dumps(
            {sid: v.value for sid, v in candidate_verdicts.items()},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_root / "fleet_verdict.json").write_text(
        json.dumps(
            {
                "fleet_verdict": fleet_verdict.value,
                "fleet_status": fleet_status.value,
                "economic_validity_offline_gate_pass": gate_pass,
                "candidate_verdicts": {sid: v.value for sid, v in candidate_verdicts.items()},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_root / "authority_boundary.json").write_text(
        json.dumps(_build_authority_boundary(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "parent_manifest_verify.log").write_text(
        "\n".join(
            [
                f"PARENT_CLOSEOUT_SUFFIX={PARENT_CLOSEOUT_SUFFIX}",
                f"MANIFEST_VERIFY_RC={start_state.parent_manifest_verify_rc}",
            ]
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
                f"- scope_classification: `{SCOPE_CLASSIFICATION}`",
                f"- go_token_consumed: `{CONFIRM_GO}`",
                f"- origin_main_sha: `{start_state.origin_main_sha}`",
                f"- binding_config_digest: `{BINDING_CONFIG_DIGEST}`",
                f"- parent_closeout_suffix: `{PARENT_CLOSEOUT_SUFFIX}`",
                f"- parent_manifest_verify_rc: `{start_state.parent_manifest_verify_rc}`",
                f"- fleet_verdict: `{fleet_verdict.value}`",
                f"- fleet_status: `{fleet_status.value}`",
                f"- economic_validity_offline_gate_pass: `{gate_pass}`",
                "- runtime_authority_created: `false`",
                "",
                "## Candidate verdicts",
                "",
                *[
                    f"- `{sid}` / `{STRATEGY_VERSION}`: `{candidate_verdicts[sid].value}`"
                    for sid in FLEET_CANDIDATES
                    if sid in candidate_verdicts
                ],
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    for strategy_id in FLEET_CANDIDATES:
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

    binding_config = start_state.binding_config
    execution_config = start_state.execution_config
    staging_root = _resolve_staging_root(binding_config)
    period_policy = _load_period_policy(repo_root)

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_root = (
        durable_evidence_root
        / DURABLE_EVIDENCE_SUBDIR
        / f"{DURABLE_EVIDENCE_BUNDLE_PREFIX}_{ts_slug}"
    )
    evidence_root.mkdir(parents=True, exist_ok=False)

    narrow_root = evidence_root / "narrow_evaluation_dataset" / "inst-eth-usdt-perp" / "v2"
    narrow_dataset = materialize_narrow_evaluation_dataset_v0(
        staging_root=staging_root,
        output_root=narrow_root,
        period_policy=period_policy,
    )

    versioned_by_id = {
        str(b["candidate_id"]): b
        for b in binding_config.get("versioned_bindings", [])
        if isinstance(b, Mapping)
    }

    candidate_results: list[CandidateExecutionResultV0] = []
    candidate_records: dict[str, dict[str, Any]] = {}
    candidate_verdicts: dict[str, CandidateEconomicVerdict] = {}
    config_dir = evidence_root / "RUNTIME_STEP31F_CONFIGS"

    for strategy_id in FLEET_CANDIDATES:
        versioned_binding = versioned_by_id.get(strategy_id, {})
        config_path = build_post_pr4922_runtime_step31f_config_v0(
            repo_root=repo_root,
            strategy_id=strategy_id,
            narrow_dataset=narrow_dataset,
            versioned_binding=versioned_binding,
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
        candidate_records[strategy_id] = materialize_candidate_result_v0(
            strategy_id=strategy_id,
            candidate_dir=candidate_dir,
            result=result,
            versioned_binding=versioned_binding,
            verdict=verdict,
            evidence_payload=evidence_payload,
        )

    fleet_status = resolve_fleet_terminal_status_v0(candidate_results)
    fleet_verdict = classify_fleet_verdict_v0(list(candidate_verdicts.values()))
    gate_pass = fleet_verdict is FleetEconomicVerdict.FLEET_ECONOMIC_VALIDITY_PASS

    ratification_stub = {
        "operator_scope_ratification_ref": BINDING_CONFIG_REL,
        "ratification_digest": BINDING_CONFIG_DIGEST,
        "fleet_binding_digest": BINDING_CONFIG_DIGEST,
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
        binding_config=binding_config,
        candidate_records=candidate_records,
        candidate_verdicts=candidate_verdicts,
        fleet_verdict=fleet_verdict,
        fleet_status=fleet_status,
        gate_pass=gate_pass,
    )

    for name, payload in (
        ("execution_config_v0.json", execution_config),
        ("binding_config_v0.json", binding_config),
    ):
        (evidence_root / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    from scripts.ops import primary_evidence_retention_v0 as retention

    manifest_rc, _msg = retention.finalize_durable_bundle_manifest(evidence_root)

    return ScopeExecutionResultV0(
        execution_config=execution_config,
        binding_config=binding_config,
        candidate_results=tuple(candidate_results),
        candidate_verdicts=candidate_verdicts,
        fleet_verdict=fleet_verdict,
        fleet_status=fleet_status,
        economic_validity_offline_gate_pass=gate_pass,
        manifest_verify_rc=manifest_rc,
        evidence_root=evidence_root,
        process_classification=PROCESS_CLASSIFICATION,
    )
