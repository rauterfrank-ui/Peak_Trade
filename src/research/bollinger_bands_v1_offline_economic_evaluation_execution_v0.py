"""Bollinger bands v1 offline economic evaluation execution v0 owner.

Bounded offline evaluation adapter reusing trade-ledger/equity-curve persistence
execution infrastructure for ratified final-research-fleet candidate bollinger_bands/v1.
No runtime, order, credentials, arming, or authority effect.
"""

from __future__ import annotations

from pathlib import Path

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

PACKAGE_MARKER = "BOLLINGER_BANDS_V1_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0=true"

SCHEMA_VERSION = "bollinger_bands_v1_offline_economic_evaluation_execution.v0"
EXECUTION_ID = "bollinger_bands_v1_offline_economic_evaluation_execution_v0"
EXECUTION_VERSION = "v0"

OPERATOR_GO = "GO_BOLLINGER_BANDS_V1_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
SCOPE_CLASSIFICATION = "BOLLINGER_BANDS_V1_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
EXPECTED_ORIGIN_MAIN_SHA = "119ddad7444fdb3238bec490faaa9430122d985d"

STRATEGY_BINDING_REF = "bollinger_bands/v1"
STRATEGY_BINDING_DIGEST = "b7d5e1d7bbdd23134285aea337ae645a8cd8b0af17286e317ae60f1860f71451"
STRATEGY_ID = "bollinger_bands"
STRATEGY_VERSION = "v1"
PRIMARY_FAILURE_CLASS = "TRADE_COUNT_BELOW_THRESHOLD"

BINDING_MATERIALIZATION_CONFIG_REL = "config/research/bollinger_bands_v1_offline_economic_evaluation_execution_binding_materialization_v0.json"
PARAMETER_BINDING_REL = (
    "config/ops/step31f_okx_inst_eth_usdt_perp_bollinger_bands_v1_economic_evaluation_v1.json"
)

DURABLE_EVIDENCE_BUNDLE_PREFIX = "bollinger_bands_v1_offline_economic_evaluation_execution_v0"

BOLLINGER_PERSISTENCE_EXECUTION_SCOPE_V0 = PersistenceExecutionScopeV0(
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


def run_bollinger_bands_execution_v0(
    *,
    confirm: str,
    repo_root: Path,
    durable_evidence_root: Path,
    binding_config_path: Path | None = None,
    require_clean_worktree: bool = True,
) -> ExecutionResultV0:
    return run_execution_v0(
        confirm=confirm,
        repo_root=repo_root,
        durable_evidence_root=durable_evidence_root,
        binding_config_path=binding_config_path,
        require_clean_worktree=require_clean_worktree,
        scope=BOLLINGER_PERSISTENCE_EXECUTION_SCOPE_V0,
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
    "BOLLINGER_PERSISTENCE_EXECUTION_SCOPE_V0",
    "PersistenceExecutionVerdict",
    "verify_preconditions_v0",
    "verify_binding_materialization_preflight_v0",
    "run_bollinger_bands_execution_v0",
    "ExecutionResultV0",
    "assert_execution_not_authorized_v0",
    "FAIL_CLOSED_REASON",
    "EXECUTION_AUTHORIZED",
    "DEFAULT_DURABLE_ARCHIVE_ROOT",
]
