"""Cross-sectional funding-rate delta momentum v0 offline evaluation infrastructure execution v0.

Infrastructure-only runner surface. Does not execute economic evaluation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.research.cross_sectional_funding_rate_delta_momentum_ranking_semantics_binding_validator_v0 import (
    ValidationVerdict,
    validate_funding_rate_delta_momentum_ranking_semantics_binding_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_bound_panel_dataset_materialization_v0 import (
    MaterializationTerminalStatus,
    materialization_result_to_dict,
    materialize_bound_funding_panel_dataset_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_scope_ratification_v0 import (
    ValidationVerdictEnum,
    validate_funding_delta_momentum_offline_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_versioned_research_binding_v0 import (
    AUTHORITY_EFFECT,
    CONFIG_REL_PATH,
    ORDER_EFFECT,
    RUNTIME_EFFECT,
    STRATEGY_ID,
    STRATEGY_VERSION,
    materialize_versioned_research_binding_v0,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_FUNDING_RATE_DELTA_MOMENTUM_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0=true"
)
SCHEMA_VERSION = (
    "cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_execution.v0"
)
EXECUTION_ID = (
    "cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_execution_v0"
)
EXECUTION_VERSION = "v0"
CONFIG_REL_PATH_OPS = (
    "config/ops/cross_sectional_funding_rate_delta_momentum_v0_economic_evaluation_v1.json"
)
INFRASTRUCTURE_GO_TOKEN = (
    "GO_BOUNDED_PRE_EVALUATION_PANEL_EXTENSION_AND_IMPLEMENTATION_SCOPE_RATIFICATION_V0"
)
RUNNER_OWNER = "scripts.ops.run_cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_execution_v0"


class InfrastructureTerminalStatus(str, Enum):
    EXECUTION_INFRASTRUCTURE_COMPLETE = "EXECUTION_INFRASTRUCTURE_COMPLETE"
    FAIL_CLOSED_BOUND_DATA_UNAVAILABLE = "FAIL_CLOSED_BOUND_DATA_UNAVAILABLE"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True)
class StartStateVerificationResultV0:
    valid: bool
    fail_reasons: tuple[str, ...]
    origin_main_sha: str
    binding_digest: str
    ratification_digest: str


@dataclass(frozen=True)
class InfrastructureReadinessResultV0:
    status: InfrastructureTerminalStatus
    execution_infrastructure_complete: bool
    panel_wiring_complete: bool
    bound_dataset_materialized: bool
    dataset_period_match: bool
    panel_data_digest: str
    reason_codes: tuple[str, ...]
    authority_effect: str
    runtime_effect: str
    economic_evaluation_executed: bool


@dataclass(frozen=True)
class EvaluationEntrypointDryRunResultV0:
    status: str
    precheck_passed: bool
    economic_evaluation_executed: bool
    stage_wiring_complete: bool
    fail_reasons: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_versioned_research_binding_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONFIG_REL_PATH
    if not path.is_file():
        return materialize_versioned_research_binding_v0()
    return json.loads(path.read_text(encoding="utf-8"))


def verify_execution_start_state_v0(
    *,
    repo_root: Path,
    ratification: Mapping[str, Any],
    versioned_binding: Mapping[str, Any] | None = None,
    origin_main_sha: str = "",
) -> StartStateVerificationResultV0:
    reasons: list[str] = []
    envelope = dict(versioned_binding or load_versioned_research_binding_v0(repo_root))
    validation = validate_funding_rate_delta_momentum_ranking_semantics_binding_v0(
        envelope["binding"]
    )
    if not validation.valid or validation.verdict != ValidationVerdict.ACCEPTED_COMPLETE:
        reasons.extend(validation.fail_reasons or ("BINDING_INCOMPLETE",))

    ratification_validation = (
        validate_funding_delta_momentum_offline_evaluation_scope_ratification_v0(
            ratification, expected_binding=envelope
        )
    )
    if ratification_validation.verdict != ValidationVerdictEnum.ACCEPTED:
        reasons.extend(ratification_validation.fail_reasons)

    config_path = repo_root / CONFIG_REL_PATH_OPS
    if not config_path.is_file():
        reasons.append("MISSING_OPS_EVALUATION_CONFIG")

    return StartStateVerificationResultV0(
        valid=not reasons,
        fail_reasons=tuple(reasons),
        origin_main_sha=origin_main_sha,
        binding_digest=str(envelope.get("binding_digest", "")),
        ratification_digest=str(ratification.get("ratification_digest", "")),
    )


def run_full_evaluation_entrypoint_dry_run_v0(
    *,
    repo_root: Path,
    ratification: Mapping[str, Any],
    staging_root: Path,
    versioned_binding: Mapping[str, Any],
    go_token: str,
) -> EvaluationEntrypointDryRunResultV0:
    if go_token != INFRASTRUCTURE_GO_TOKEN:
        return EvaluationEntrypointDryRunResultV0(
            status="FAIL_CLOSED_PRECHECK",
            precheck_passed=False,
            economic_evaluation_executed=False,
            stage_wiring_complete=False,
            fail_reasons=("GO_TOKEN_INVALID",),
        )
    start = verify_execution_start_state_v0(
        repo_root=repo_root,
        ratification=ratification,
        versioned_binding=versioned_binding,
    )
    if not start.valid:
        return EvaluationEntrypointDryRunResultV0(
            status="FAIL_CLOSED_PRECHECK",
            precheck_passed=False,
            economic_evaluation_executed=False,
            stage_wiring_complete=False,
            fail_reasons=start.fail_reasons,
        )
    materialization = materialize_bound_funding_panel_dataset_v0(
        staging_root,
        period_binding=versioned_binding["period_binding"],
        expected_data_digest=versioned_binding["data_digest"],
    )
    if materialization.status is not MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE:
        return EvaluationEntrypointDryRunResultV0(
            status="FAIL_CLOSED_PRECHECK",
            precheck_passed=False,
            economic_evaluation_executed=False,
            stage_wiring_complete=False,
            fail_reasons=materialization.reason_codes,
        )
    return EvaluationEntrypointDryRunResultV0(
        status="ENTRYPOINT_READY_DRY_RUN_STOPPED",
        precheck_passed=True,
        economic_evaluation_executed=False,
        stage_wiring_complete=True,
        fail_reasons=(),
    )


def materialize_infrastructure_summary_v0(
    *,
    ratification: Mapping[str, Any],
    readiness: InfrastructureReadinessResultV0,
    origin_main_sha: str,
    execution_bundle_dir: str,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "execution_id": EXECUTION_ID,
        "execution_version": EXECUTION_VERSION,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "ratification_digest": ratification.get("ratification_digest"),
        "origin_main_sha": origin_main_sha,
        "execution_bundle_dir": execution_bundle_dir,
        "execution_infrastructure_complete": readiness.execution_infrastructure_complete,
        "panel_wiring_complete": readiness.panel_wiring_complete,
        "bound_dataset_materialized": readiness.bound_dataset_materialized,
        "dataset_period_match": readiness.dataset_period_match,
        "panel_data_digest": readiness.panel_data_digest,
        "infrastructure_status": readiness.status.value,
        "reason_codes": list(readiness.reason_codes),
        "economic_evaluation_executed": False,
        "economic_classification": "NONE",
        "ready_for_separately_authorized_offline_economic_evaluation": (
            readiness.status is InfrastructureTerminalStatus.EXECUTION_INFRASTRUCTURE_COMPLETE
            and readiness.bound_dataset_materialized
        ),
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "config_rel_path": CONFIG_REL_PATH_OPS,
        "candidate_binding_ref": CONFIG_REL_PATH,
    }
    body["manifest_digest"] = _stable_digest(body)
    return body


def entrypoint_result_to_dict(result: EvaluationEntrypointDryRunResultV0) -> dict[str, Any]:
    return {
        "status": result.status,
        "precheck_passed": result.precheck_passed,
        "economic_evaluation_executed": result.economic_evaluation_executed,
        "stage_wiring_complete": result.stage_wiring_complete,
        "fail_reasons": list(result.fail_reasons),
    }
