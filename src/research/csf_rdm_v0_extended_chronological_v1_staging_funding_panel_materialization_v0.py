"""CSF/RDM v0 extended_chronological_v1 staging and bound funding panel materialization v0.

Bounded offline dataset/funding readiness scope only. Reuses canonical preflight
owners and assesses staging readiness. Does not auto-start Full-Universe OKX fetch,
economic evaluation, runtime, credentials, or order effects.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.research.cross_sectional_funding_rate_delta_momentum_v0_bound_panel_dataset_materialization_v0 import (
    MaterializationTerminalStatus,
    materialization_result_to_dict,
    materialize_bound_funding_panel_dataset_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_execution_v0 import (
    resolve_actual_repo_shas_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_versioned_research_binding_v0 import (
    PANEL_CALENDAR_END_UTC,
    PANEL_CALENDAR_START_UTC,
    materialize_versioned_research_binding_v0,
)
from src.research.csf_rdm_v0_dataset_funding_binding_materialization_preflight_v0 import (
    preflight_result_to_dict,
    run_dataset_funding_binding_materialization_preflight_v0,
)

PACKAGE_MARKER = (
    "CSF_RDM_V0_EXTENDED_CHRONOLOGICAL_V1_STAGING_FUNDING_PANEL_MATERIALIZATION_V0=true"
)
MATERIALIZATION_VERSION = (
    "csf_rdm_v0_extended_chronological_v1_staging_funding_panel_materialization.v0"
)
CONFIRM_GO = "GO_BOUNDED_CSF_RDM_V0_EXTENDED_CHRONOLOGICAL_V1_STAGING_AND_BOUND_FUNDING_PANEL_MATERIALIZATION_V0"
CONFIG_REL_PATH = (
    "config/ops/csf_rdm_v0_extended_chronological_v1_staging_funding_panel_materialization_v0.json"
)

DEFAULT_STAGING_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/extended_chronological_v1"
)

CANONICAL_DATASET_OWNER = "scripts/ops/fetch_cross_sectional_funding_rate_delta_momentum_v0_extended_chronological_panel_v0.py"
CANONICAL_FUNDING_OWNER = "scripts/ops/materialize_cross_sectional_funding_rate_delta_momentum_v0_bound_panel_funding_dataset_v0.py"
CANONICAL_PREFLIGHT_OWNER = (
    "scripts/ops/run_csf_rdm_v0_dataset_funding_binding_materialization_preflight_v0.py"
)

REASON_MISSING_CANONICAL_STAGING_ROOT = "MISSING_CANONICAL_EXTENDED_CHRONOLOGICAL_V1_STAGING_ROOT"
REASON_STAGING_MISSING = "STAGING_MISSING"
REASON_MISSING_FUNDING_MANIFEST = "MISSING_BOUND_FUNDING_PANEL_MANIFEST"
REASON_MISSING_FUNDING_BARS = "MISSING_BOUND_FUNDING_PANEL_BARS"
REASON_FUNDING_MISSING = "FUNDING_MISSING"
REASON_MATERIALIZATION_INCOMPLETE = "BOUND_FUNDING_PANEL_MATERIALIZATION_INCOMPLETE"
REASON_FULL_UNIVERSE_FETCH_NOT_AUTHORIZED = "FULL_UNIVERSE_FETCH_NOT_AUTHORIZED"
REASON_FULL_UNIVERSE_FETCH_REQUIRES_EXPLICIT_OPERATOR_GO = (
    "FULL_UNIVERSE_FETCH_REQUIRES_EXPLICIT_OPERATOR_GO"
)
REASON_SEPARATE_BOUNDED_MATERIALIZATION_SCOPE_REQUIRED = (
    "SEPARATE_BOUNDED_OFFLINE_PANEL_MATERIALIZATION_SCOPE_REQUIRED"
)
SAFE_NEXT_ACTION_BOUNDED_OFFLINE_MATERIALIZATION = (
    "RUN_SEPARATE_BOUNDED_OFFLINE_PANEL_MATERIALIZATION_FROM_RAW_SOURCE_THEN_FUNDING_PANEL"
)


class StagingReadinessStatus(str, Enum):
    READY = "READY"
    FAIL_CLOSED_MISSING_PRECONDITION = "FAIL_CLOSED_MISSING_PRECONDITION"


class MaterializationScopeVerdict(str, Enum):
    PREFLIGHT_GATE_PASS_READY_FOR_NEXT_PRE_EVALUATION_GATE = (
        "PREFLIGHT_GATE_PASS_READY_FOR_NEXT_PRE_EVALUATION_GATE"
    )
    FAIL_CLOSED_STAGING_OR_FUNDING_NOT_MATERIALIZED = (
        "FAIL_CLOSED_STAGING_OR_FUNDING_NOT_MATERIALIZED"
    )
    FAIL_CLOSED_PREFLIGHT = "FAIL_CLOSED_PREFLIGHT"


@dataclass(frozen=True)
class StagingReadinessAssessmentV0:
    status: StagingReadinessStatus
    staging_root: str
    staging_root_exists: bool
    funding_manifest_exists: bool
    funding_bars_exists: bool
    materialization_status: str | None
    materialization_ready: bool
    reason_codes: tuple[str, ...]
    safe_next_action: str


@dataclass(frozen=True)
class MaterializationScopeResultV0:
    verdict: MaterializationScopeVerdict
    staging_assessment: StagingReadinessAssessmentV0
    fetch_result: dict[str, Any] | None
    funding_result: dict[str, Any] | None
    preflight_status: str
    preflight_payload: dict[str, Any]
    ready_for_next_pre_evaluation_gate: bool
    economic_evaluation_executed: bool
    economic_evaluation_blocked: bool
    reason_codes: tuple[str, ...]
    origin_main_binding: str
    binding_origin_main_sha: str


def load_materialization_binding_config_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONFIG_REL_PATH
    if not path.is_file():
        return {
            "schema_version": MATERIALIZATION_VERSION,
            "staging_root": str(DEFAULT_STAGING_ROOT),
            "dataset_owner": CANONICAL_DATASET_OWNER,
            "funding_owner": CANONICAL_FUNDING_OWNER,
            "preflight_owner": CANONICAL_PREFLIGHT_OWNER,
            "panel_calendar_start_utc": PANEL_CALENDAR_START_UTC,
            "panel_calendar_end_utc": PANEL_CALENDAR_END_UTC,
        }
    return json.loads(path.read_text(encoding="utf-8"))


def assess_staging_readiness_v0(
    staging_root: Path,
    *,
    versioned_binding: Mapping[str, Any] | None = None,
) -> StagingReadinessAssessmentV0:
    """Read-only assessment of canonical extended_chronological_v1 staging readiness."""
    staging_root = staging_root.resolve()
    binding = dict(versioned_binding or materialize_versioned_research_binding_v0())
    reasons: list[str] = []

    staging_exists = staging_root.is_dir()
    funding_manifest = staging_root / "panel" / "panel_funding_dataset_manifest.json"
    funding_bars = staging_root / "panel" / "normalized_panel_bars_with_funding.json"
    manifest_exists = funding_manifest.is_file()
    bars_exists = funding_bars.is_file()

    if not staging_exists:
        reasons.append(REASON_MISSING_CANONICAL_STAGING_ROOT)
        reasons.append(REASON_STAGING_MISSING)
    if staging_exists and not manifest_exists:
        reasons.append(REASON_MISSING_FUNDING_MANIFEST)
        reasons.append(REASON_FUNDING_MISSING)
    if staging_exists and not bars_exists:
        reasons.append(REASON_MISSING_FUNDING_BARS)
        if REASON_FUNDING_MISSING not in reasons:
            reasons.append(REASON_FUNDING_MISSING)

    materialization_status: str | None = None
    materialization_ready = False
    if staging_exists and manifest_exists and bars_exists:
        materialization = materialize_bound_funding_panel_dataset_v0(
            staging_root,
            period_binding=binding["period_binding"],
            expected_data_digest=str(binding["data_digest"]),
        )
        materialization_status = materialization.status.value
        materialization_ready = (
            materialization.status is MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE
            and materialization.data_digest_match
            and bool(materialization.funding_manifest_path)
        )
        if not materialization_ready:
            reasons.extend(materialization.reason_codes)
            reasons.append(REASON_MATERIALIZATION_INCOMPLETE)

    if materialization_ready and not reasons:
        status = StagingReadinessStatus.READY
        safe_next = "RUN_PREFLIGHT_AND_VERIFY_DIGEST_BINDINGS"
    else:
        status = StagingReadinessStatus.FAIL_CLOSED_MISSING_PRECONDITION
        safe_next = SAFE_NEXT_ACTION_BOUNDED_OFFLINE_MATERIALIZATION

    return StagingReadinessAssessmentV0(
        status=status,
        staging_root=str(staging_root),
        staging_root_exists=staging_exists,
        funding_manifest_exists=manifest_exists,
        funding_bars_exists=bars_exists,
        materialization_status=materialization_status,
        materialization_ready=materialization_ready,
        reason_codes=tuple(dict.fromkeys(reasons)),
        safe_next_action=safe_next,
    )


def _patch_funding_manifest_extension(staging_root: Path) -> None:
    manifest_path = staging_root / "panel" / "panel_funding_dataset_manifest.json"
    if not manifest_path.is_file():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["dataset_extension"] = "extended_chronological_with_funding_v1"
    manifest["panel_id"] = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def attempt_staging_and_funding_materialization_v0(
    *,
    staging_root: Path,
    durable_evidence_root: Path,
    attempt_fetch: bool,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, tuple[str, ...]]:
    """Assess staging/funding readiness without implicit Full-Universe network fetch.

    ``attempt_fetch=True`` does not authorize network I/O in this scope. It fails
    closed with ``FULL_UNIVERSE_FETCH_REQUIRES_EXPLICIT_OPERATOR_GO`` and directs
    operators to a separate bounded offline panel materialization scope.
    """
    _ = durable_evidence_root
    reasons: list[str] = []
    staging_root = staging_root.resolve()

    if staging_root.is_dir():
        assessment = assess_staging_readiness_v0(staging_root)
        if assessment.materialization_ready:
            return None, {"verdict": "BOUND_FUNDING_PANEL_READY_REUSED"}, ()
        reasons.extend(assessment.reason_codes)
        if not attempt_fetch:
            reasons.append("STAGING_PRESENT_BUT_FUNDING_NOT_READY")
            return None, None, tuple(dict.fromkeys(reasons))

    if not staging_root.is_dir():
        reasons.append(REASON_MISSING_CANONICAL_STAGING_ROOT)
        reasons.append(REASON_STAGING_MISSING)

    if attempt_fetch:
        reasons.extend(
            (
                REASON_FULL_UNIVERSE_FETCH_REQUIRES_EXPLICIT_OPERATOR_GO,
                REASON_FULL_UNIVERSE_FETCH_NOT_AUTHORIZED,
                REASON_SEPARATE_BOUNDED_MATERIALIZATION_SCOPE_REQUIRED,
            )
        )

    return None, None, tuple(dict.fromkeys(reasons))


def run_materialization_scope_v0(
    *,
    repo_root: Path,
    staging_root: Path,
    durable_evidence_root: Path,
    binding_origin_main_sha: str | None = None,
    attempt_fetch: bool = False,
    versioned_binding: Mapping[str, Any] | None = None,
) -> MaterializationScopeResultV0:
    """Assess staging/funding readiness and run preflight without evaluation."""
    _, actual_origin_main = resolve_actual_repo_shas_v0(repo_root)
    resolved_binding_sha = (binding_origin_main_sha or actual_origin_main).strip()
    binding = dict(versioned_binding or materialize_versioned_research_binding_v0())

    assessment_before = assess_staging_readiness_v0(staging_root, versioned_binding=binding)
    fetch_result: dict[str, Any] | None = None
    funding_result: dict[str, Any] | None = None
    materialization_reasons: tuple[str, ...] = ()

    if assessment_before.status is not StagingReadinessStatus.READY:
        fetch_result, funding_result, materialization_reasons = (
            attempt_staging_and_funding_materialization_v0(
                staging_root=staging_root,
                durable_evidence_root=durable_evidence_root,
                attempt_fetch=attempt_fetch,
            )
        )

    assessment_after = assess_staging_readiness_v0(staging_root, versioned_binding=binding)
    preflight = run_dataset_funding_binding_materialization_preflight_v0(
        repo_root=repo_root,
        staging_root=staging_root,
        expected_origin_main_sha=resolved_binding_sha,
        binding_origin_main_sha=resolved_binding_sha,
        versioned_binding=binding,
    )
    preflight_payload = preflight_result_to_dict(preflight)

    ready = preflight.ready_for_next_pre_evaluation_gate
    if ready:
        verdict = MaterializationScopeVerdict.PREFLIGHT_GATE_PASS_READY_FOR_NEXT_PRE_EVALUATION_GATE
        reason_codes: tuple[str, ...] = ()
    elif assessment_after.status is not StagingReadinessStatus.READY:
        verdict = MaterializationScopeVerdict.FAIL_CLOSED_STAGING_OR_FUNDING_NOT_MATERIALIZED
        reason_codes = tuple(
            dict.fromkeys(
                (
                    *assessment_after.reason_codes,
                    *materialization_reasons,
                    *preflight.reason_codes,
                )
            )
        )
    else:
        verdict = MaterializationScopeVerdict.FAIL_CLOSED_PREFLIGHT
        reason_codes = preflight.reason_codes

    return MaterializationScopeResultV0(
        verdict=verdict,
        staging_assessment=assessment_after,
        fetch_result=fetch_result,
        funding_result=funding_result,
        preflight_status=preflight.status.value,
        preflight_payload=preflight_payload,
        ready_for_next_pre_evaluation_gate=ready,
        economic_evaluation_executed=False,
        economic_evaluation_blocked=True,
        reason_codes=reason_codes,
        origin_main_binding=actual_origin_main,
        binding_origin_main_sha=resolved_binding_sha,
    )


def materialization_scope_result_to_dict(
    result: MaterializationScopeResultV0,
    *,
    preflight_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": MATERIALIZATION_VERSION,
        "verdict": result.verdict.value,
        "confirm_go": CONFIRM_GO,
        "package_marker": PACKAGE_MARKER,
        "origin_main_binding": result.origin_main_binding,
        "binding_origin_main_sha": result.binding_origin_main_sha,
        "staging_assessment": {
            "status": result.staging_assessment.status.value,
            "staging_root": result.staging_assessment.staging_root,
            "staging_root_exists": result.staging_assessment.staging_root_exists,
            "funding_manifest_exists": result.staging_assessment.funding_manifest_exists,
            "funding_bars_exists": result.staging_assessment.funding_bars_exists,
            "materialization_status": result.staging_assessment.materialization_status,
            "materialization_ready": result.staging_assessment.materialization_ready,
            "reason_codes": list(result.staging_assessment.reason_codes),
            "safe_next_action": result.staging_assessment.safe_next_action,
        },
        "fetch_result": result.fetch_result,
        "funding_result": result.funding_result,
        "preflight_status": result.preflight_status,
        "preflight": result.preflight_payload,
        "ready_for_next_pre_evaluation_gate": result.ready_for_next_pre_evaluation_gate,
        "economic_evaluation_executed": result.economic_evaluation_executed,
        "economic_evaluation_blocked": result.economic_evaluation_blocked,
        "reason_codes": list(result.reason_codes),
        "reuse_decisions": {
            "dataset_owner": CANONICAL_DATASET_OWNER,
            "funding_owner": CANONICAL_FUNDING_OWNER,
            "preflight_owner": CANONICAL_PREFLIGHT_OWNER,
            "materialize_bound_funding_panel_dataset_v0": (
                "src/research/cross_sectional_funding_rate_delta_momentum_v0_"
                "bound_panel_dataset_materialization_v0.py"
            ),
        },
    }


def staging_assessment_to_dict(assessment: StagingReadinessAssessmentV0) -> dict[str, Any]:
    return {
        "status": assessment.status.value,
        "staging_root": assessment.staging_root,
        "staging_root_exists": assessment.staging_root_exists,
        "funding_manifest_exists": assessment.funding_manifest_exists,
        "funding_bars_exists": assessment.funding_bars_exists,
        "materialization_status": assessment.materialization_status,
        "materialization_ready": assessment.materialization_ready,
        "reason_codes": list(assessment.reason_codes),
        "safe_next_action": assessment.safe_next_action,
    }


__all__ = [
    "CANONICAL_DATASET_OWNER",
    "CANONICAL_FUNDING_OWNER",
    "CANONICAL_PREFLIGHT_OWNER",
    "CONFIG_REL_PATH",
    "DEFAULT_STAGING_ROOT",
    "CONFIRM_GO",
    "MATERIALIZATION_VERSION",
    "MaterializationScopeResultV0",
    "MaterializationScopeVerdict",
    "REASON_FULL_UNIVERSE_FETCH_NOT_AUTHORIZED",
    "REASON_FULL_UNIVERSE_FETCH_REQUIRES_EXPLICIT_OPERATOR_GO",
    "REASON_FUNDING_MISSING",
    "REASON_STAGING_MISSING",
    "SAFE_NEXT_ACTION_BOUNDED_OFFLINE_MATERIALIZATION",
    "StagingReadinessAssessmentV0",
    "StagingReadinessStatus",
    "assess_staging_readiness_v0",
    "attempt_staging_and_funding_materialization_v0",
    "load_materialization_binding_config_v0",
    "materialization_scope_result_to_dict",
    "run_materialization_scope_v0",
    "staging_assessment_to_dict",
]
