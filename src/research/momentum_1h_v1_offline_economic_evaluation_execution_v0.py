"""Momentum 1h v1 offline economic evaluation execution v0 owner.

Bounded offline evaluation adapter reusing trade-ledger/equity-curve persistence
execution infrastructure for ratified final-research-fleet candidate momentum_1h/v1.
No runtime, order, credentials, arming, or authority effect.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.research.trade_ledger_equity_curve_persistence_offline_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    DEFAULT_DURABLE_ARCHIVE_ROOT,
    EVIDENCE_CLASS_ID,
    EXECUTION_AUTHORIZED,
    FAIL_CLOSED_REASON,
    ORDER_EFFECT,
    RUNTIME_EFFECT,
    ExecutionResultV0,
    PersistenceExecutionScopeV0,
    PersistenceExecutionVerdict,
    assert_execution_not_authorized_v0,
    run_execution_v0,
    verify_binding_materialization_preflight_v0,
    verify_preconditions_v0,
)

PACKAGE_MARKER = "MOMENTUM_1H_V1_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0=true"

SCHEMA_VERSION = "momentum_1h_v1_offline_economic_evaluation_execution.v0"
EXECUTION_ID = "momentum_1h_v1_offline_economic_evaluation_execution_v0"
EXECUTION_VERSION = "v0"

OPERATOR_GO = "GO_MOMENTUM_1H_V1_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
SCOPE_CLASSIFICATION = "MOMENTUM_1H_V1_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
EXPECTED_ORIGIN_MAIN_SHA = "bda1e4e92e1352e65fd2f2cf0d3aca9e44328ccc"

STRATEGY_BINDING_REF = "momentum_1h/v1"
STRATEGY_BINDING_DIGEST = "a8b7d87100d7167205258056144690273cda54769c9c29fcf8e91d4477318730"
STRATEGY_ID = "momentum_1h"
STRATEGY_VERSION = "v1"
PRIMARY_FAILURE_CLASS = "TRADE_COUNT_BELOW_THRESHOLD"

SCOPE_BINDING_CONFIG_REL = "config/research/momentum_1h_v1_offline_economic_evaluation_scope_and_binding_materialization_v0.json"
BINDING_MATERIALIZATION_CONFIG_REL = "config/research/momentum_1h_v1_offline_economic_evaluation_execution_binding_materialization_v0.json"
PARAMETER_BINDING_REL = (
    "config/ops/step31f_okx_inst_eth_usdt_perp_momentum_1h_v1_economic_evaluation_v1.json"
)

DURABLE_EVIDENCE_BUNDLE_PREFIX = "momentum_1h_v1_offline_economic_evaluation_execution_v0"

MOMENTUM_PERSISTENCE_EXECUTION_SCOPE_V0 = PersistenceExecutionScopeV0(
    operator_go=OPERATOR_GO,
    scope_classification=SCOPE_CLASSIFICATION,
    expected_origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    strategy_binding_ref=STRATEGY_BINDING_REF,
    strategy_binding_digest=STRATEGY_BINDING_DIGEST,
    strategy_id=STRATEGY_ID,
    strategy_version=STRATEGY_VERSION,
    primary_failure_class=PRIMARY_FAILURE_CLASS,
    binding_materialization_config_rel=BINDING_MATERIALIZATION_CONFIG_REL,
    parameter_binding_rel=PARAMETER_BINDING_REL,
    execution_id=EXECUTION_ID,
    durable_evidence_bundle_prefix=DURABLE_EVIDENCE_BUNDLE_PREFIX,
    schema_version=SCHEMA_VERSION,
)


def _write_required_execution_artifacts_v0(
    *,
    evidence_root: Path,
    result: ExecutionResultV0,
) -> None:
    """Materialize canonical METRICS_SUMMARY / EVALUATION_CONTEXT / CHECKS_SUMMARY artifacts."""
    metrics = dict(result.metric_summary)
    metrics.update(
        {
            "promotion_eligible": False,
            "runtime_rewire_admissible": False,
            "authority_effect": AUTHORITY_EFFECT,
            "process_execution_pass": result.verdict != PersistenceExecutionVerdict.INCONCLUSIVE,
            "economic_validity_offline_gate_pass": metrics.get(
                "economic_validity_offline_gate_pass", False
            ),
        }
    )
    (evidence_root / "METRICS_SUMMARY.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    evaluation_context: dict[str, Any] = {
        "schema_version": "momentum_1h_v1_offline_economic_evaluation_execution_context.v0",
        "scope_classification": SCOPE_CLASSIFICATION,
        "go_token_consumed": OPERATOR_GO,
        "strategy_binding_ref": STRATEGY_BINDING_REF,
        "strategy_binding_digest": STRATEGY_BINDING_DIGEST,
        "scope_binding_config_ref": SCOPE_BINDING_CONFIG_REL,
        "execution_binding_config_ref": BINDING_MATERIALIZATION_CONFIG_REL,
        "parameter_binding_ref": PARAMETER_BINDING_REL,
        "origin_main_sha": result.origin_main_sha,
        "evaluation_id": result.evaluation_summary.get("evaluation_id"),
        "durable_evidence_root": str(evidence_root),
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_authorized": False,
        "promotion_eligible": False,
        "runtime_rewire_admissible": False,
        "evaluation_execution_authorized": False,
        "offline_only": True,
    }
    (evidence_root / "EVALUATION_CONTEXT.json").write_text(
        json.dumps(evaluation_context, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    checks_summary = {
        "schema_version": "momentum_1h_v1_offline_economic_evaluation_checks_summary.v0",
        "manifest_verify_rc": result.manifest_verify_rc,
        "process_verdict": result.verdict.value,
        "trade_count": result.trade_count,
        "equity_point_count": result.equity_point_count,
        "fail_reasons": list(result.fail_reasons),
        "repo_jsonl_leak": False,
        "authority_effect": AUTHORITY_EFFECT,
    }
    (evidence_root / "CHECKS_SUMMARY.json").write_text(
        json.dumps(checks_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_momentum_1h_execution_v0(
    *,
    confirm: str,
    repo_root: Path,
    durable_evidence_root: Path,
    binding_config_path: Path | None = None,
    require_clean_worktree: bool = True,
) -> ExecutionResultV0:
    binding_path = binding_config_path or (repo_root / BINDING_MATERIALIZATION_CONFIG_REL)
    result = run_execution_v0(
        confirm=confirm,
        repo_root=repo_root,
        durable_evidence_root=durable_evidence_root,
        binding_config_path=binding_path,
        require_clean_worktree=require_clean_worktree,
        scope=MOMENTUM_PERSISTENCE_EXECUTION_SCOPE_V0,
    )
    _write_required_execution_artifacts_v0(
        evidence_root=result.evidence_root,
        result=result,
    )
    from scripts.ops import primary_evidence_retention_v0 as retention  # noqa: PLC0415

    manifest_rc, manifest_msg = retention.finalize_durable_bundle_manifest(result.evidence_root)
    if manifest_rc != 0:
        raise ValueError(f"MANIFEST_VERIFY_FAILED:{manifest_msg}")
    return ExecutionResultV0(
        verdict=result.verdict,
        evidence_root=result.evidence_root,
        manifest_verify_rc=manifest_rc,
        trade_ledger_path=result.trade_ledger_path,
        equity_curve_path=result.equity_curve_path,
        trade_count=result.trade_count,
        equity_point_count=result.equity_point_count,
        metric_summary=result.metric_summary,
        evaluation_summary=result.evaluation_summary,
        origin_main_sha=result.origin_main_sha,
        fail_reasons=result.fail_reasons,
    )


__all__ = [
    "OPERATOR_GO",
    "SCOPE_CLASSIFICATION",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "AUTHORITY_EFFECT",
    "RUNTIME_EFFECT",
    "ORDER_EFFECT",
    "EVIDENCE_CLASS_ID",
    "STRATEGY_BINDING_DIGEST",
    "STRATEGY_BINDING_REF",
    "SCOPE_BINDING_CONFIG_REL",
    "BINDING_MATERIALIZATION_CONFIG_REL",
    "MOMENTUM_PERSISTENCE_EXECUTION_SCOPE_V0",
    "PersistenceExecutionVerdict",
    "verify_preconditions_v0",
    "verify_binding_materialization_preflight_v0",
    "run_momentum_1h_execution_v0",
    "ExecutionResultV0",
    "assert_execution_not_authorized_v0",
    "FAIL_CLOSED_REASON",
    "EXECUTION_AUTHORIZED",
    "DEFAULT_DURABLE_ARCHIVE_ROOT",
]
