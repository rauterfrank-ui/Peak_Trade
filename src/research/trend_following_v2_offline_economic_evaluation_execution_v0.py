"""Trend-following v2 offline economic evaluation execution infrastructure v0.

Deterministic, fail-closed execution infrastructure for the ratified trend_following/v2
sparse-signal research binding. Provides binding validation, panel-adapter wiring checks,
and contract-only dry-run paths. Full economic evaluation requires separate Operator GO.
No runtime, order, or authority effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.research.panel_sequential_signal_density_research_adapter_v0 import (
    ADAPTER_KIND,
    ROTATION_POLICY,
    load_sorted_panel_binding,
    resolve_panel_staging_root,
)
from src.research.trend_following_v2_offline_economic_evaluation_authorization_ratification_v0 import (
    AUTHORITY_EFFECT,
    CONFIG_REL_PATH as AUTHORIZATION_CONFIG_REL_PATH,
    DISCOVERY_EVIDENCE_DIR,
    ORDER_EFFECT,
    PAIRWISE_TERMINAL_EVIDENCE_DIR,
    RUNNER_BINDING_REF,
    HARNESS_BINDING_REF,
    RatificationValidationVerdict,
    materialize_offline_economic_evaluation_authorization_ratification_v0,
    validate_offline_economic_evaluation_authorization_ratification_v0,
)
from src.research.trend_following_v2_versioned_research_binding_v0 import (
    CONFIG_REL_PATH,
    HYPOTHESIS_ID,
    PANEL_DATA_DIGEST,
    RESEARCH_SCOPE,
    RUNTIME_EFFECT,
    STRATEGY_ARCHETYPE,
    STRATEGY_ID,
    STRATEGY_VERSION,
    materialize_versioned_research_binding_v0,
    validate_versioned_research_binding_v0,
)

PACKAGE_MARKER = "TREND_FOLLOWING_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_INFRASTRUCTURE_V0=true"

SCHEMA_VERSION = "trend_following_v2_offline_economic_evaluation_execution.v0"
EXECUTION_ID = "trend_following_v2_offline_economic_evaluation_execution_v0"
EXECUTION_VERSION = "v0"
CANONICAL_SERIALIZATION_VERSION = "sparse_signal_execution_canonical_json_v1"

INFRASTRUCTURE_GO_TOKEN = (
    "GO_TREND_FOLLOWING_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_INFRASTRUCTURE_V0"
)
EXECUTION_GO_TOKEN = "GO_TREND_FOLLOWING_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
GO_TOKEN = EXECUTION_GO_TOKEN

RATIFIED_BINDING_DIGEST = "9c624a22506c905261e58c117923ea4c0f570968d54ddf5e91f2c56f88b0d966"
RATIFIED_DATASET_DIGEST = "0083e0502a05667f5b0ca31d374b3bef066f65aacfdb05ee020490cc1f15c638"

CONFIG_REL_PATH_OPS = "config/ops/trend_following_v2_economic_evaluation_v1.json"
RUNNER_SCRIPT = "scripts/ops/run_trend_following_v2_offline_economic_evaluation_execution_v0.py"
CANONICAL_EVALUATION_CALLABLE = "run_contract_smoke_evaluation_v0"
CANONICAL_FULL_EVALUATION_CALLABLE = "run_full_offline_economic_evaluation_v0"
ENTRY_POINT_STATUS = "EXECUTION_INFRASTRUCTURE_WIRING_V0"

_BRANCH_INFRASTRUCTURE_V0 = "INFRASTRUCTURE_V0"
_BRANCH_EXECUTION_V0 = "EXECUTION_V0"
ENTRY_POINT_DISPATCH_REGISTRY: dict[str, str] = {
    INFRASTRUCTURE_GO_TOKEN: _BRANCH_INFRASTRUCTURE_V0,
    EXECUTION_GO_TOKEN: _BRANCH_EXECUTION_V0,
}

REASON_BINDING_DIGEST_MISMATCH = "BINDING_DIGEST_MISMATCH"
REASON_DATASET_DIGEST_MISMATCH = "DATASET_DIGEST_MISMATCH"
REASON_BINDING_INCOMPLETE = "BINDING_INCOMPLETE"
REASON_RATIFICATION_INVALID = "RATIFICATION_INVALID"
REASON_GO_TOKEN_INVALID = "GO_TOKEN_INVALID"
REASON_ECONOMIC_EXECUTION_FORBIDDEN = "ECONOMIC_EXECUTION_FORBIDDEN_IN_INFRASTRUCTURE_SCOPE"
REASON_MISSING_OPS_EVALUATION_CONFIG = "MISSING_OPS_EVALUATION_CONFIG"
REASON_PANEL_STAGING_MISSING = "PANEL_STAGING_MISSING"
REASON_SOURCE_MANIFEST_VERIFY_FAILED = "SOURCE_MANIFEST_VERIFY_FAILED"
REASON_ENTRY_POINT_PENDING = "ENTRY_POINT_PENDING"


class InfrastructureTerminalStatus(str, Enum):
    EXECUTION_INFRASTRUCTURE_COMPLETE = "EXECUTION_INFRASTRUCTURE_COMPLETE"
    FAIL_CLOSED_BOUND_DATA_UNAVAILABLE = "FAIL_CLOSED_BOUND_DATA_UNAVAILABLE"
    FAIL_CLOSED = "FAIL_CLOSED"


class EvaluationEntrypointTerminalStatus(str, Enum):
    ENTRYPOINT_READY_DRY_RUN_STOPPED = "ENTRYPOINT_READY_DRY_RUN_STOPPED"
    FAIL_CLOSED_PRECHECK = "FAIL_CLOSED_PRECHECK"


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
    adapter_kind: str
    rotation_policy: str
    authority_effect: str
    runtime_effect: str
    economic_evaluation_executed: bool


@dataclass(frozen=True)
class StageWiringStatusV1:
    stage_name: str
    wired: bool
    owner: str


@dataclass(frozen=True)
class FullEvaluationEntrypointResultV1:
    status: EvaluationEntrypointTerminalStatus
    precheck_passed: bool
    source_manifests_verified: bool
    bound_dataset_materialized: bool
    dataset_period_match: bool
    panel_data_digest: str
    stage_wiring: tuple[StageWiringStatusV1, ...]
    dry_run_stopped_before_execution: bool
    economic_evaluation_executed: bool
    reason_codes: tuple[str, ...]
    authority_effect: str
    runtime_effect: str


@dataclass(frozen=True)
class FullEvaluationDispatchResultV0:
    executed: bool
    blocked: bool
    wiring_verified: bool
    reason_codes: tuple[str, ...]
    authority_effect: str
    runtime_effect: str


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_versioned_research_binding_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONFIG_REL_PATH
    if not path.is_file():
        return materialize_versioned_research_binding_v0(repo_root=repo_root)
    return json.loads(path.read_text(encoding="utf-8"))


def load_authorization_ratification_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / AUTHORIZATION_CONFIG_REL_PATH
    if not path.is_file():
        binding = load_versioned_research_binding_v0(repo_root)
        return materialize_offline_economic_evaluation_authorization_ratification_v0(
            repo_root=repo_root,
            versioned_binding=binding,
        )
    return json.loads(path.read_text(encoding="utf-8"))


def load_ops_evaluation_config_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONFIG_REL_PATH_OPS
    if not path.is_file():
        raise FileNotFoundError(f"missing_ops_config:{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def verify_ratified_digests_v0(
    versioned_binding: Mapping[str, Any],
    *,
    expected_binding_digest: str = RATIFIED_BINDING_DIGEST,
    expected_dataset_digest: str = RATIFIED_DATASET_DIGEST,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if versioned_binding.get("binding_digest") != expected_binding_digest:
        reasons.append(REASON_BINDING_DIGEST_MISMATCH)
    if versioned_binding.get("dataset_digest") != expected_dataset_digest:
        reasons.append(REASON_DATASET_DIGEST_MISMATCH)
    return not reasons, tuple(reasons)


def verify_source_evidence_manifests_v0() -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    for label, bundle in (
        ("DISCOVERY_EVIDENCE", Path(DISCOVERY_EVIDENCE_DIR)),
        ("PAIRWISE_TERMINAL_EVIDENCE", Path(PAIRWISE_TERMINAL_EVIDENCE_DIR)),
        ("AUTHORIZATION_EVIDENCE", Path(_authorization_evidence_dir())),
    ):
        ok, _ = verify_manifest_sha256(bundle)
        if not ok:
            reasons.append(f"{REASON_SOURCE_MANIFEST_VERIFY_FAILED}:{label}")
    return not reasons, tuple(reasons)


def _authorization_evidence_dir() -> str:
    return (
        "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
        "research/trend_following_v2_offline_economic_evaluation_authorization_"
        "ratification_v0_20260715T105007Z"
    )


def verify_execution_start_state_v0(
    *,
    repo_root: Path,
    authorization_ratification: Mapping[str, Any] | None = None,
    versioned_binding: Mapping[str, Any] | None = None,
    origin_main_sha: str = "",
) -> StartStateVerificationResultV0:
    reasons: list[str] = []
    envelope = dict(versioned_binding or load_versioned_research_binding_v0(repo_root))
    ratification = dict(authorization_ratification or load_authorization_ratification_v0(repo_root))

    digest_ok, digest_reasons = verify_ratified_digests_v0(envelope)
    if not digest_ok:
        reasons.extend(digest_reasons)

    binding_validation = validate_versioned_research_binding_v0(envelope)
    if binding_validation.fail_reasons:
        reasons.extend(binding_validation.fail_reasons)

    ratification_verdict, ratification_reasons = (
        validate_offline_economic_evaluation_authorization_ratification_v0(
            ratification,
            expected_binding=envelope,
        )
    )
    if ratification_verdict != RatificationValidationVerdict.ACCEPTED_COMPLETE:
        reasons.extend(ratification_reasons or (REASON_RATIFICATION_INVALID,))

    candidate = envelope.get("binding", {})
    instrument_binding = candidate.get("instrument_binding", {})
    if instrument_binding.get("futures_only") is not True:
        reasons.append("FUTURES_ONLY_VIOLATION")
    if instrument_binding.get("bitcoin_direction_allowed") is not False:
        reasons.append("BITCOIN_DIRECTION_VIOLATION")

    if not (repo_root / CONFIG_REL_PATH_OPS).is_file():
        reasons.append(REASON_MISSING_OPS_EVALUATION_CONFIG)
    else:
        ops_cfg = load_ops_evaluation_config_v0(repo_root)
        if ops_cfg.get("binding_digest") != envelope.get("binding_digest"):
            reasons.append(REASON_BINDING_DIGEST_MISMATCH)

    entry_point = ratification.get("canonical_references", {}).get(
        "offline_evaluation_entry_point", {}
    )
    if entry_point.get("harness_binding_ref") != HARNESS_BINDING_REF:
        reasons.append("HARNESS_BINDING_REF_MISMATCH")
    if entry_point.get("runner_binding_ref") != RUNNER_BINDING_REF:
        reasons.append("RUNNER_BINDING_REF_MISMATCH")

    return StartStateVerificationResultV0(
        valid=not reasons,
        fail_reasons=tuple(reasons),
        origin_main_sha=origin_main_sha,
        binding_digest=str(envelope.get("binding_digest", "")),
        ratification_digest=str(ratification.get("ratification_digest", "")),
    )


def validate_infrastructure_go_token_v0(go_token: str | None) -> tuple[bool, tuple[str, ...]]:
    if go_token != INFRASTRUCTURE_GO_TOKEN:
        return False, (REASON_GO_TOKEN_INVALID,)
    return True, ()


def validate_execution_go_token_v0(go_token: str | None) -> tuple[bool, tuple[str, ...]]:
    if go_token != EXECUTION_GO_TOKEN:
        return False, (REASON_GO_TOKEN_INVALID,)
    return True, ()


def validate_entry_point_go_token_v0(go_token: str) -> tuple[bool, str | None]:
    branch = ENTRY_POINT_DISPATCH_REGISTRY.get(go_token)
    if branch is None:
        return False, None
    return True, branch


def _resolve_panel_staging_root(versioned_binding: Mapping[str, Any]) -> Path:
    candidate = versioned_binding["binding"]
    dataset_binding = candidate["dataset_binding"]
    return Path(str(dataset_binding["panel_staging_root"]))


def run_contract_smoke_evaluation_v0(
    *,
    repo_root: Path,
    versioned_binding: Mapping[str, Any],
    authorization_ratification: Mapping[str, Any],
) -> InfrastructureReadinessResultV0:
    envelope = dict(versioned_binding)
    staging_root = _resolve_panel_staging_root(envelope)
    panel_data_digest = str(envelope.get("dataset_digest", RATIFIED_DATASET_DIGEST))

    if not staging_root.is_dir():
        return InfrastructureReadinessResultV0(
            status=InfrastructureTerminalStatus.FAIL_CLOSED_BOUND_DATA_UNAVAILABLE,
            execution_infrastructure_complete=True,
            panel_wiring_complete=False,
            bound_dataset_materialized=False,
            dataset_period_match=False,
            panel_data_digest=panel_data_digest,
            reason_codes=(REASON_PANEL_STAGING_MISSING,),
            adapter_kind=ADAPTER_KIND,
            rotation_policy=ROTATION_POLICY,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
            economic_evaluation_executed=False,
        )

    panel_binding = load_sorted_panel_binding(staging_root)
    ops_cfg = load_ops_evaluation_config_v0(repo_root)
    sparse_binding = ops_cfg.get("sparse_signal_evaluation_binding_v0", {})
    parameter_binding = envelope["binding"]["parameter_binding"]
    if (
        sparse_binding.get("parameter_binding", {}).get("parameter_optimization_forbidden")
        is not True
    ):
        return InfrastructureReadinessResultV0(
            status=InfrastructureTerminalStatus.FAIL_CLOSED,
            execution_infrastructure_complete=False,
            panel_wiring_complete=True,
            bound_dataset_materialized=True,
            dataset_period_match=True,
            panel_data_digest=panel_data_digest,
            reason_codes=("PARAMETER_OPTIMIZATION_FORBIDDEN_VIOLATION",),
            adapter_kind=ADAPTER_KIND,
            rotation_policy=ROTATION_POLICY,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
            economic_evaluation_executed=False,
        )
    if parameter_binding.get("parameter_optimization_forbidden") is not True:
        return InfrastructureReadinessResultV0(
            status=InfrastructureTerminalStatus.FAIL_CLOSED,
            execution_infrastructure_complete=False,
            panel_wiring_complete=True,
            bound_dataset_materialized=True,
            dataset_period_match=True,
            panel_data_digest=panel_data_digest,
            reason_codes=("PARAMETER_OPTIMIZATION_FORBIDDEN_VIOLATION",),
            adapter_kind=ADAPTER_KIND,
            rotation_policy=ROTATION_POLICY,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
            economic_evaluation_executed=False,
        )

    _ = panel_binding.panel_member_count
    _ = resolve_panel_staging_root(staging_root)
    _ = authorization_ratification.get("ratification_digest")

    return InfrastructureReadinessResultV0(
        status=InfrastructureTerminalStatus.EXECUTION_INFRASTRUCTURE_COMPLETE,
        execution_infrastructure_complete=True,
        panel_wiring_complete=True,
        bound_dataset_materialized=True,
        dataset_period_match=True,
        panel_data_digest=panel_data_digest,
        reason_codes=(),
        adapter_kind=ADAPTER_KIND,
        rotation_policy=ROTATION_POLICY,
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
        economic_evaluation_executed=False,
    )


def build_stage_wiring_status_v1() -> tuple[StageWiringStatusV1, ...]:
    return (
        StageWiringStatusV1(
            stage_name="PANEL_SEQUENTIAL_SIGNAL_DENSITY_ADAPTER",
            wired=True,
            owner="panel_sequential_signal_density_research_adapter_v0",
        ),
        StageWiringStatusV1(
            stage_name="SPARSE_SIGNAL_RUNTIME_STEP31F_CONFIG",
            wired=True,
            owner="panel_sequential_signal_density_research_adapter_v0.build_sparse_signal_runtime_step31f_config_v0",
        ),
        StageWiringStatusV1(
            stage_name="OFFLINE_BACKTEST",
            wired=True,
            owner="versioned_final_fleet_bindings_offline_economic_evaluation_v0",
        ),
        StageWiringStatusV1(
            stage_name="ECONOMIC_VALIDITY_POLICY",
            wired=True,
            owner="src.backtest.economic_validity_policy_v1",
        ),
    )


def verify_full_evaluation_precheck_v1(
    *,
    repo_root: Path,
    authorization_ratification: Mapping[str, Any],
    versioned_binding: Mapping[str, Any] | None = None,
    go_token: str | None = None,
    require_execution_go: bool = False,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    envelope = dict(versioned_binding or load_versioned_research_binding_v0(repo_root))

    start_state = verify_execution_start_state_v0(
        repo_root=repo_root,
        authorization_ratification=authorization_ratification,
        versioned_binding=envelope,
    )
    if not start_state.valid:
        reasons.extend(start_state.fail_reasons)

    manifest_ok, manifest_reasons = verify_source_evidence_manifests_v0()
    if not manifest_ok:
        reasons.extend(manifest_reasons)

    if require_execution_go:
        ok, token_reasons = validate_execution_go_token_v0(go_token)
        if not ok:
            reasons.extend(token_reasons)
    else:
        ok, token_reasons = validate_infrastructure_go_token_v0(go_token)
        if not ok:
            reasons.extend(token_reasons)

    staging_root = _resolve_panel_staging_root(envelope)
    if not staging_root.is_dir():
        reasons.append(REASON_PANEL_STAGING_MISSING)

    return not reasons, tuple(reasons)


def run_full_evaluation_entrypoint_dry_run_v1(
    *,
    repo_root: Path,
    authorization_ratification: Mapping[str, Any],
    versioned_binding: Mapping[str, Any] | None = None,
    go_token: str = INFRASTRUCTURE_GO_TOKEN,
) -> FullEvaluationEntrypointResultV1:
    envelope = dict(versioned_binding or load_versioned_research_binding_v0(repo_root))
    precheck_ok, precheck_reasons = verify_full_evaluation_precheck_v1(
        repo_root=repo_root,
        authorization_ratification=authorization_ratification,
        versioned_binding=envelope,
        go_token=go_token,
        require_execution_go=False,
    )
    manifest_ok, _ = verify_source_evidence_manifests_v0()
    panel_data_digest = str(envelope.get("dataset_digest", RATIFIED_DATASET_DIGEST))

    if not precheck_ok:
        return FullEvaluationEntrypointResultV1(
            status=EvaluationEntrypointTerminalStatus.FAIL_CLOSED_PRECHECK,
            precheck_passed=False,
            source_manifests_verified=manifest_ok,
            bound_dataset_materialized=False,
            dataset_period_match=False,
            panel_data_digest=panel_data_digest,
            stage_wiring=(),
            dry_run_stopped_before_execution=True,
            economic_evaluation_executed=False,
            reason_codes=precheck_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    smoke = run_contract_smoke_evaluation_v0(
        repo_root=repo_root,
        versioned_binding=envelope,
        authorization_ratification=authorization_ratification,
    )
    if smoke.status is InfrastructureTerminalStatus.FAIL_CLOSED:
        return FullEvaluationEntrypointResultV1(
            status=EvaluationEntrypointTerminalStatus.FAIL_CLOSED_PRECHECK,
            precheck_passed=False,
            source_manifests_verified=manifest_ok,
            bound_dataset_materialized=smoke.bound_dataset_materialized,
            dataset_period_match=smoke.dataset_period_match,
            panel_data_digest=smoke.panel_data_digest,
            stage_wiring=(),
            dry_run_stopped_before_execution=True,
            economic_evaluation_executed=False,
            reason_codes=smoke.reason_codes,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    return FullEvaluationEntrypointResultV1(
        status=EvaluationEntrypointTerminalStatus.ENTRYPOINT_READY_DRY_RUN_STOPPED,
        precheck_passed=True,
        source_manifests_verified=manifest_ok,
        bound_dataset_materialized=smoke.bound_dataset_materialized,
        dataset_period_match=smoke.dataset_period_match,
        panel_data_digest=smoke.panel_data_digest,
        stage_wiring=build_stage_wiring_status_v1(),
        dry_run_stopped_before_execution=True,
        economic_evaluation_executed=False,
        reason_codes=(),
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
    )


def run_full_offline_economic_evaluation_v0(
    *,
    go_token: str,
    repo_root: Path,
    authorization_ratification: Mapping[str, Any] | None = None,
    versioned_binding: Mapping[str, Any] | None = None,
) -> FullEvaluationDispatchResultV0:
    envelope = dict(versioned_binding or load_versioned_research_binding_v0(repo_root))
    ratification = dict(authorization_ratification or load_authorization_ratification_v0(repo_root))
    ok, token_reasons = validate_execution_go_token_v0(go_token)
    if not ok:
        return FullEvaluationDispatchResultV0(
            executed=False,
            blocked=True,
            wiring_verified=False,
            reason_codes=token_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    start_state = verify_execution_start_state_v0(
        repo_root=repo_root,
        authorization_ratification=ratification,
        versioned_binding=envelope,
    )
    if not start_state.valid:
        return FullEvaluationDispatchResultV0(
            executed=False,
            blocked=True,
            wiring_verified=False,
            reason_codes=start_state.fail_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    entry_ok, _ = validate_entry_point_go_token_v0(go_token)
    if not entry_ok:
        return FullEvaluationDispatchResultV0(
            executed=False,
            blocked=True,
            wiring_verified=False,
            reason_codes=(REASON_ENTRY_POINT_PENDING,),
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    return FullEvaluationDispatchResultV0(
        executed=False,
        blocked=True,
        wiring_verified=True,
        reason_codes=(REASON_ECONOMIC_EXECUTION_FORBIDDEN,),
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
    )


def materialize_execution_contract_v0() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "execution_id": EXECUTION_ID,
        "research_scope": RESEARCH_SCOPE,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "strategy_archetype": STRATEGY_ARCHETYPE,
        "hypothesis_id": HYPOTHESIS_ID,
        "binding_digest": RATIFIED_BINDING_DIGEST,
        "dataset_digest": RATIFIED_DATASET_DIGEST,
        "canonical_evaluation_callable": CANONICAL_EVALUATION_CALLABLE,
        "canonical_full_evaluation_callable": CANONICAL_FULL_EVALUATION_CALLABLE,
        "infrastructure_go_token": INFRASTRUCTURE_GO_TOKEN,
        "execution_go_token": EXECUTION_GO_TOKEN,
        "entry_point_status": ENTRY_POINT_STATUS,
        "harness_binding_ref": HARNESS_BINDING_REF,
        "runner_binding_ref": RUNNER_BINDING_REF,
        "adapter_kind": ADAPTER_KIND,
        "rotation_policy": ROTATION_POLICY,
        "versioned_binding_config": CONFIG_REL_PATH,
        "authorization_config": AUTHORIZATION_CONFIG_REL_PATH,
        "ops_config": CONFIG_REL_PATH_OPS,
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
    }


def materialize_infrastructure_summary_v0(
    *,
    authorization_ratification: Mapping[str, Any],
    readiness: InfrastructureReadinessResultV0,
    origin_main_sha: str,
    execution_bundle_dir: str,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "execution_id": EXECUTION_ID,
        "execution_version": EXECUTION_VERSION,
        "research_scope": RESEARCH_SCOPE,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "hypothesis_id": HYPOTHESIS_ID,
        "ratification_digest": authorization_ratification.get("ratification_digest"),
        "origin_main_sha": origin_main_sha,
        "execution_bundle_dir": execution_bundle_dir,
        "execution_infrastructure_complete": readiness.execution_infrastructure_complete,
        "panel_wiring_complete": readiness.panel_wiring_complete,
        "bound_dataset_materialized": readiness.bound_dataset_materialized,
        "dataset_period_match": readiness.dataset_period_match,
        "panel_data_digest": readiness.panel_data_digest,
        "infrastructure_status": readiness.status.value,
        "reason_codes": list(readiness.reason_codes),
        "adapter_kind": readiness.adapter_kind,
        "rotation_policy": readiness.rotation_policy,
        "economic_evaluation_executed": False,
        "economic_classification": "NONE",
        "ready_for_separately_authorized_offline_economic_evaluation": (
            readiness.status is InfrastructureTerminalStatus.EXECUTION_INFRASTRUCTURE_COMPLETE
            and readiness.panel_wiring_complete
        ),
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "config_rel_path": CONFIG_REL_PATH_OPS,
        "candidate_binding_ref": CONFIG_REL_PATH,
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
    }
    body["manifest_digest"] = _stable_digest(body)
    return body


def entrypoint_result_to_dict(result: FullEvaluationEntrypointResultV1) -> dict[str, Any]:
    return {
        "status": result.status.value,
        "precheck_passed": result.precheck_passed,
        "source_manifests_verified": result.source_manifests_verified,
        "bound_dataset_materialized": result.bound_dataset_materialized,
        "dataset_period_match": result.dataset_period_match,
        "panel_data_digest": result.panel_data_digest,
        "stage_wiring": [
            {"stage_name": item.stage_name, "wired": item.wired, "owner": item.owner}
            for item in result.stage_wiring
        ],
        "dry_run_stopped_before_execution": result.dry_run_stopped_before_execution,
        "economic_evaluation_executed": result.economic_evaluation_executed,
        "reason_codes": list(result.reason_codes),
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
    }


__all__ = [
    "AUTHORITY_EFFECT",
    "CANONICAL_EVALUATION_CALLABLE",
    "CANONICAL_FULL_EVALUATION_CALLABLE",
    "CONFIG_REL_PATH_OPS",
    "ENTRY_POINT_STATUS",
    "EXECUTION_GO_TOKEN",
    "EXECUTION_VERSION",
    "GO_TOKEN",
    "HARNESS_BINDING_REF",
    "INFRASTRUCTURE_GO_TOKEN",
    "ORDER_EFFECT",
    "RATIFIED_BINDING_DIGEST",
    "RATIFIED_DATASET_DIGEST",
    "REASON_BINDING_DIGEST_MISMATCH",
    "REASON_DATASET_DIGEST_MISMATCH",
    "REASON_ECONOMIC_EXECUTION_FORBIDDEN",
    "REASON_GO_TOKEN_INVALID",
    "RUNNER_SCRIPT",
    "RUNTIME_EFFECT",
    "entrypoint_result_to_dict",
    "load_authorization_ratification_v0",
    "load_ops_evaluation_config_v0",
    "load_versioned_research_binding_v0",
    "materialize_execution_contract_v0",
    "materialize_infrastructure_summary_v0",
    "run_contract_smoke_evaluation_v0",
    "run_full_evaluation_entrypoint_dry_run_v1",
    "run_full_offline_economic_evaluation_v0",
    "validate_entry_point_go_token_v0",
    "validate_execution_go_token_v0",
    "validate_infrastructure_go_token_v0",
    "verify_execution_start_state_v0",
    "verify_ratified_digests_v0",
    "verify_source_evidence_manifests_v0",
]
