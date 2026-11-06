"""Authority-Map-/Atlas-guided whole-system G2 primary causal E2E (post #6938 main).

Traces legitimate PAPER|SHADOW|TESTNET primary-evidence producers, discovers admissible
durable archives, preserves Case B anti-laundering, and continues G2→M4–M8 only on
explicitly classified primary input.

RUNTIME_AUTHORIZATION_EFFECT=NONE
PRODUCTIVE_OPTIMIZATION_JOIN_AUTHORIZED=false
EXTERNAL_EFFECT=false
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Final, Mapping, Sequence

from src.experiments.canonical_m4_m8_evidence_return_loop_v1 import LOOP_STATUS_COMPLETE
from scripts.ops.primary_evidence_retention_v0 import (
    BOUNDED_SHADOW_DURABLE_RUN_REQUIRED_REL_PATHS,
    BOUNDED_TESTNET_DURABLE_RUN_REQUIRED_REL_PATHS,
    PAPER_BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS,
    validate_durable_primary_evidence_root,
)
from src.governance.governed_productive_learning_to_g2_primary_evidence_causal_closure_v1 import (
    G2_PRIMARY_SUPPORTED_MODES,
    prove_semantic_adjudication_case_b_invariants_v1,
    run_legitimate_g2_primary_to_m4_m8_reference_continuation_v1,
)
from src.governance.governed_runtime_g2_to_m4_m8_real_mechanical_continuation_v1 import (
    G2RuntimeM4M8ContinuationRequestV1,
    run_g2_runtime_to_m4_m8_evidence_return_continuation_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    GovernedRuntimePrimaryProjectionRequestV1,
    RuntimePrimarySourceModeV1,
    validate_primary_evidence_for_projection_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    PRODUCTIVE_OPTIMIZATION_JOIN_AUTHORIZED,
)

SCHEMA_VERSION: Final[str] = (
    "governed_authority_map_atlas_guided_whole_system_g2_primary_causal_e2e_v1"
)
WORKPACKAGE_ID: Final[str] = (
    "AUTHORITY_MAP_ATLAS_GUIDED_WHOLE_SYSTEM_CAUSAL_E2E_FROM_POST_6938_MAIN"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/AUTHORITY_MAP_ATLAS_GUIDED_WHOLE_SYSTEM_CAUSAL_E2E_FROM_POST_6938_MAIN_V1.md"
)
MAP_SOURCE_REL: Final[str] = (
    "config/governance/current_system_interaction_authority_map_v1/source_v1.json"
)
ATLAS_CENSUS_REL: Final[str] = "docs/system_atlas/census/census_meta.yaml"

FIXTURE_RUN_ID: Final[str] = "g2_projection_fixture_v1"
FIXTURE_STRATEGY_VERSION: Final[str] = "strategy_g2_fixture_v1"

PAPER_PRODUCER: Final[str] = (
    "scripts.ops.run_paper_only_bounded_observation_adapter_v0"
    "+ scripts.ops.review_paper_bounded_observation_evidence_v0"
)
SHADOW_PRODUCER: Final[str] = (
    "scripts.ops.review_shadow_bounded_observation_evidence_v0+ shadow_247 bounded wrapper lane"
)
TESTNET_PRODUCER: Final[str] = (
    "scripts.ops.review_testnet_bounded_observation_evidence_v0"
    "+ bounded testnet connectivity adapters"
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


class PrimaryArchiveClassificationV1(str, Enum):
    OBSERVED_BOUNDED_RUNTIME = "OBSERVED_BOUNDED_RUNTIME"
    FIXTURE_OR_SYNTHETIC = "FIXTURE_OR_SYNTHETIC"
    INVALID = "INVALID"
    UNKNOWN = "UNKNOWN"


class TriStateV1(str, Enum):
    TRUE = "true"
    FALSE = "false"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class LifecycleProducerReportV1:
    lifecycle: str
    producer: str
    authority: str
    runtime_wired: TriStateV1
    runtime_reachable: TriStateV1
    admission_satisfied: TriStateV1
    external_effect_required: TriStateV1
    durable_primary_archive_produced: TriStateV1
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class DiscoveredPrimaryArchiveV1:
    root: Path
    classification: PrimaryArchiveClassificationV1
    source_execution_mode: str | None
    validate_ok: bool
    projection_admit_ok: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class G2M8ContinuationEvidenceV1:
    primary_archive_valid: bool
    g2_ingress_admitted: bool
    g2_projection_reached: bool
    g2_binding_reached: bool
    real_runtime_g2_reached: bool
    m4_reached: bool
    m5_reached: bool
    m6_reached: bool
    m7_reached: bool
    m8_reached: bool
    classification: str
    reason_codes: tuple[str, ...]


def repo_head_sha_prefix(repo_root: Path | None = None) -> str:
    root = repo_root or _REPO_ROOT
    try:
        full = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()[
            :16
        ]
        return full.lower()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def _read_run_metadata(root: Path) -> dict[str, Any] | None:
    path = root / "RUN_METADATA.json"
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _required_rel_paths_for_mode(mode: str | None) -> tuple[str, ...]:
    if mode == "PAPER":
        return PAPER_BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS
    if mode == "SHADOW":
        return BOUNDED_SHADOW_DURABLE_RUN_REQUIRED_REL_PATHS
    if mode == "TESTNET":
        return BOUNDED_TESTNET_DURABLE_RUN_REQUIRED_REL_PATHS
    return PAPER_BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS


def classify_primary_archive_root_v1(
    root: Path,
    *,
    repo_root: Path | None = None,
) -> DiscoveredPrimaryArchiveV1:
    root = root.resolve()
    meta = _read_run_metadata(root)
    mode = str(meta.get("source_execution_mode") or "").upper() if meta else None
    required = _required_rel_paths_for_mode(mode)
    ok, _msg, _detail = validate_durable_primary_evidence_root(root, required_rel_paths=required)
    reasons: list[str] = []
    if not ok:
        reasons.append("DURABLE_VALIDATE_FAIL")
        return DiscoveredPrimaryArchiveV1(
            root=root,
            classification=PrimaryArchiveClassificationV1.INVALID,
            source_execution_mode=mode,
            validate_ok=False,
            projection_admit_ok=False,
            reason_codes=tuple(reasons),
        )
    run_id = str(meta.get("run_id") or "") if meta else ""
    strategy_version = str(meta.get("strategy_version") or "") if meta else ""
    sha_prefix = str(meta.get("repo_head_sha_prefix") or "").lower() if meta else ""
    current_prefix = repo_head_sha_prefix(repo_root)
    if run_id == FIXTURE_RUN_ID or strategy_version == FIXTURE_STRATEGY_VERSION:
        reasons.append("FIXTURE_RUN_ID_OR_STRATEGY")
        classification = PrimaryArchiveClassificationV1.FIXTURE_OR_SYNTHETIC
    elif sha_prefix and current_prefix and sha_prefix != current_prefix:
        if sha_prefix == "0123456789abcdef":
            reasons.append("CANONICAL_TEST_SHA_PREFIX")
            classification = PrimaryArchiveClassificationV1.FIXTURE_OR_SYNTHETIC
        else:
            reasons.append("REPO_SHA_PREFIX_MISMATCH")
            classification = PrimaryArchiveClassificationV1.UNKNOWN
    elif mode not in G2_PRIMARY_SUPPORTED_MODES:
        reasons.append("UNSUPPORTED_SOURCE_EXECUTION_MODE")
        classification = PrimaryArchiveClassificationV1.INVALID
    else:
        classification = PrimaryArchiveClassificationV1.OBSERVED_BOUNDED_RUNTIME
        reasons.append("DURABLE_VALIDATE_PASS_NON_FIXTURE_METADATA")
    proj_ok = False
    if mode in G2_PRIMARY_SUPPORTED_MODES:
        admit, code, _d = validate_primary_evidence_for_projection_v1(
            source_mode=RuntimePrimarySourceModeV1(mode),
            primary_evidence_root=root,
        )
        proj_ok = admit
        if not admit and code:
            reasons.append(f"PROJECTION_{code}")
    return DiscoveredPrimaryArchiveV1(
        root=root,
        classification=classification,
        source_execution_mode=mode,
        validate_ok=True,
        projection_admit_ok=proj_ok,
        reason_codes=tuple(dict.fromkeys(reasons)),
    )


def discover_primary_archives_under_evidence_ops_v1(
    *,
    repo_root: Path | None = None,
    max_roots: int = 64,
) -> tuple[DiscoveredPrimaryArchiveV1, ...]:
    root = repo_root or _REPO_ROOT
    evidence_ops = root / "evidence" / "ops"
    if not evidence_ops.is_dir():
        return ()
    found: list[DiscoveredPrimaryArchiveV1] = []
    for meta_path in evidence_ops.rglob("RUN_METADATA.json"):
        if len(found) >= max_roots:
            break
        archive_root = meta_path.parent
        found.append(classify_primary_archive_root_v1(archive_root, repo_root=root))
    return tuple(found)


def _paper_admission_notes(repo_root: Path) -> tuple[str, ...]:
    return (
        "PAPER_BOUNDED_EXECUTE_REQUIRES_APPROVAL_RECORD",
        "APPROVE_EXECUTE_PAPER_ONLY_120MIN_NOW=true",
        "START_PAPER_NOW=true",
        "DEFAULT_DURATION_SECONDS=7200",
        "STRICT_REPO_CLEAN_DEFAULT_BLOCKS_UNTRACKED_EVIDENCE_WORKTREE",
    )


def adjudicate_lifecycle_primary_producers_v1(
    *,
    repo_root: Path | None = None,
    observed_runtime_archive_found: bool,
) -> tuple[LifecycleProducerReportV1, LifecycleProducerReportV1, LifecycleProducerReportV1]:
    root = repo_root or _REPO_ROOT
    paper_script = root / "scripts/ops/run_paper_only_bounded_observation_adapter_v0.py"
    paper_review = root / "scripts/ops/review_paper_bounded_observation_evidence_v0.py"
    shadow_review = root / "scripts/ops/review_shadow_bounded_observation_evidence_v0.py"
    testnet_review = root / "scripts/ops/review_testnet_bounded_observation_evidence_v0.py"
    paper_wired = (
        TriStateV1.TRUE if paper_script.is_file() and paper_review.is_file() else TriStateV1.FALSE
    )
    shadow_wired = TriStateV1.TRUE if shadow_review.is_file() else TriStateV1.FALSE
    testnet_wired = TriStateV1.TRUE if testnet_review.is_file() else TriStateV1.FALSE
    paper = LifecycleProducerReportV1(
        lifecycle="PAPER",
        producer=PAPER_PRODUCER,
        authority="docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md §2a.1",
        runtime_wired=paper_wired,
        runtime_reachable=TriStateV1.FALSE,
        admission_satisfied=TriStateV1.FALSE,
        external_effect_required=TriStateV1.FALSE,
        durable_primary_archive_produced=(
            TriStateV1.TRUE if observed_runtime_archive_found else TriStateV1.FALSE
        ),
        notes=_paper_admission_notes(root),
    )
    shadow = LifecycleProducerReportV1(
        lifecycle="SHADOW",
        producer=SHADOW_PRODUCER,
        authority="docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md §2a.1",
        runtime_wired=shadow_wired,
        runtime_reachable=TriStateV1.UNKNOWN,
        admission_satisfied=TriStateV1.FALSE,
        external_effect_required=TriStateV1.FALSE,
        durable_primary_archive_produced=TriStateV1.FALSE,
        notes=("SHADOW_EXECUTE_REQUIRES_SEPARATE_BOUNDED_WRAPPER_APPROVAL",),
    )
    testnet = LifecycleProducerReportV1(
        lifecycle="TESTNET",
        producer=TESTNET_PRODUCER,
        authority="Standing TESTNET_AUTHORIZED=false unless scoped Owner-GO",
        runtime_wired=testnet_wired,
        runtime_reachable=TriStateV1.FALSE,
        admission_satisfied=TriStateV1.FALSE,
        external_effect_required=TriStateV1.UNKNOWN,
        durable_primary_archive_produced=TriStateV1.FALSE,
        notes=("TESTNET_BOUNDED_LANE_NOT_EXERCISED_THIS_WP",),
    )
    return paper, shadow, testnet


def select_legitimate_observed_primary_archive_v1(
    discovered: Sequence[DiscoveredPrimaryArchiveV1],
) -> DiscoveredPrimaryArchiveV1 | None:
    for item in discovered:
        if item.classification is not PrimaryArchiveClassificationV1.OBSERVED_BOUNDED_RUNTIME:
            continue
        if not item.projection_admit_ok:
            continue
        return item
    return None


def run_g2_m8_continuation_evidence_v1(
    projection_request: GovernedRuntimePrimaryProjectionRequestV1,
    *,
    classification: str,
) -> G2M8ContinuationEvidenceV1:
    mode = projection_request.source_mode.value
    root = projection_request.primary_evidence_root
    admit, _code, _d = validate_primary_evidence_for_projection_v1(
        source_mode=projection_request.source_mode,
        primary_evidence_root=root,
    )
    val_ok, _m, _det = validate_durable_primary_evidence_root(
        root,
        required_rel_paths=_required_rel_paths_for_mode(mode),
    )
    g2 = run_g2_runtime_to_m4_m8_evidence_return_continuation_v1(
        G2RuntimeM4M8ContinuationRequestV1(projection_request=projection_request)
    )
    loop = dict(g2.m4_m8_loop or {})
    cycle = dict(loop.get("cycle") or {})
    plane_ok = bool(cycle.get("experiment_plane_result"))
    opt_ok = bool(cycle.get("optimization_experiment_evidence"))
    m8 = (
        loop.get("status") == LOOP_STATUS_COMPLETE
        and loop.get("forward_return_loop_closed") is True
    )
    binding_reached = g2.canonical_optimization_input_validated is True
    projection_reached = g2.projection is not None
    return G2M8ContinuationEvidenceV1(
        primary_archive_valid=val_ok,
        g2_ingress_admitted=admit,
        g2_projection_reached=projection_reached,
        g2_binding_reached=binding_reached,
        real_runtime_g2_reached=g2.g2_real_source_used is True,
        m4_reached=g2.m4_m8_real_ingress_reached is True and plane_ok,
        m5_reached=g2.m4_m8_real_ingress_reached is True,
        m6_reached=g2.m4_m8_evidence_return_output_produced is True,
        m7_reached=plane_ok and opt_ok,
        m8_reached=m8 and g2.m4_m8_evidence_return_output_produced is True,
        classification=classification,
        reason_codes=(f"SOURCE_MODE={mode}", f"CLASSIFICATION={classification}"),
    )


def prove_post_6938_case_b_preserved_v1(*, repo_root: Path | None = None) -> bool:
    return prove_semantic_adjudication_case_b_invariants_v1(repo_root=repo_root)


def lifecycle_report_to_mapping(report: LifecycleProducerReportV1) -> Mapping[str, Any]:
    return {
        "PRODUCER": report.producer,
        "AUTHORITY": report.authority,
        "RUNTIME_WIRED": report.runtime_wired.value,
        "RUNTIME_REACHABLE": report.runtime_reachable.value,
        "ADMISSION_SATISFIED": report.admission_satisfied.value,
        "EXTERNAL_EFFECT_REQUIRED": report.external_effect_required.value,
        "DURABLE_PRIMARY_ARCHIVE_PRODUCED": report.durable_primary_archive_produced.value,
        "NOTES": list(report.notes),
    }


def run_reference_fixture_g2_m8_control_v1(
    projection_request: GovernedRuntimePrimaryProjectionRequestV1,
) -> G2M8ContinuationEvidenceV1:
    run_legitimate_g2_primary_to_m4_m8_reference_continuation_v1(
        projection_request=projection_request,
        classification="LEGITIMATE_PRIMARY_EVIDENCE_FIXTURE_CONTROL_ONLY",
    )
    return run_g2_m8_continuation_evidence_v1(
        projection_request,
        classification="LEGITIMATE_PRIMARY_EVIDENCE_FIXTURE_CONTROL_ONLY",
    )


__all__ = [
    "ATLAS_CENSUS_REL",
    "FIXTURE_RUN_ID",
    "G2M8ContinuationEvidenceV1",
    "LifecycleProducerReportV1",
    "MAP_SOURCE_REL",
    "NORMATIVE_SPEC",
    "PAPER_PRODUCER",
    "PrimaryArchiveClassificationV1",
    "PRODUCTIVE_OPTIMIZATION_JOIN_AUTHORIZED",
    "SCHEMA_VERSION",
    "SHADOW_PRODUCER",
    "TESTNET_PRODUCER",
    "TriStateV1",
    "WORKPACKAGE_ID",
    "adjudicate_lifecycle_primary_producers_v1",
    "classify_primary_archive_root_v1",
    "discover_primary_archives_under_evidence_ops_v1",
    "lifecycle_report_to_mapping",
    "prove_post_6938_case_b_preserved_v1",
    "repo_head_sha_prefix",
    "run_g2_m8_continuation_evidence_v1",
    "run_reference_fixture_g2_m8_control_v1",
    "select_legitimate_observed_primary_archive_v1",
]
