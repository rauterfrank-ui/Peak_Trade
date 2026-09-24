"""D27 F5 shadow/numeric subfamily forensic adjudication v1 (read-only).

Decomposes F5 into F5-FRESH, F5-SURV, F5-CAP. Does not wire lifecycle enforcement, authorize
promotion, or mutate shadow/productive numeric values.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_f5_fresh_futures_input_freshness_optimizable_surface_v1 import (
    SURFACE_ID as F5_FRESH_SURFACE_ID,
)
from src.experiments.canonical_f5_shadow_per_token_calibration_test_entry_v1 import (
    build_shadow_calibration_registry_v1,
)
from src.experiments.canonical_optimization_surface_families_pre_test_preparation_v1 import (
    PreparationStatus,
    optimization_surface_family_records_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)

SCHEMA_VERSION: Final[str] = "d27_f5_shadow_test_entry_authority_subfamily_adjudication_v1"
WORKPACKAGE_ID: Final[str] = "V32_D27_F5_SHADOW_TEST_ENTRY_AUTHORITY_SUBFAMILY_ADJUDICATION_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/V32_D27_F5_SHADOW_TEST_ENTRY_AUTHORITY_SUBFAMILY_ADJUDICATION_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "v32_d27_f5_shadow_test_entry_authority_subfamily_adjudication_v1_decision_v1.json"
)

F5_SUBFAMILY_GATE_IDS: Final[tuple[str, ...]] = ("F5-FRESH", "F5-SURV", "F5-CAP")

SHADOW_CAMPAIGN_ENTRY: Final[str] = (
    "src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1."
    "campaign_runner_v1.run_shadow_campaign_v1"
)
F5_FRESH_COLLECTOR: Final[str] = (
    "src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1."
    "shadow_futures_input_freshness_age_collector_v1.collect_shadow_futures_input_freshness_age_v1"
)
ENVELOPE_RESOLVER: Final[str] = (
    "src.experiments.canonical_optimizable_envelope_v1.resolve_optimizable_envelope_v1"
)
D27_F1_F2_ENFORCEMENT: Final[str] = (
    "src.governance.d27_research_test_entry_lifecycle_enforcement_v1."
    "enforce_d27_test_entry_lifecycle_admission_v1"
)

AUTHORITY_EFFECT: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
NEW_AUTHORITY_CREATED: Final[bool] = False
TRADING_DECISION_AUTHORITY_CHANGED: Final[bool] = False
IMPLEMENTATION_PERFORMED: Final[bool] = False


class AdjudicationVerdictV1(str, Enum):
    PROVEN_CURRENT = "PROVEN_CURRENT"
    PARTIAL_CURRENT = "PARTIAL_CURRENT"
    ABSENT = "ABSENT"
    CONFLICTING = "CONFLICTING"
    UNKNOWN = "UNKNOWN"


class EpistemicClassV1(str, Enum):
    CANONICAL_AUTHORITY = "CANONICAL_AUTHORITY"
    ALREADY_ADJUDICATED = "ALREADY_ADJUDICATED"
    NAVIGATION_INDEX_ONLY = "NAVIGATION_INDEX_ONLY"
    INTERPRETATION = "INTERPRETATION"
    HYPOTHESIS = "HYPOTHESIS"
    UNKNOWN_CONFLICTING = "UNKNOWN_CONFLICTING"


class F5WiringDecisionV1(str, Enum):
    READY_FOR_BOUNDED_WIRING = "READY_FOR_BOUNDED_WIRING"
    OWNER_POLICY_REQUIRED = "OWNER_POLICY_REQUIRED"
    NOT_D27_TEST_SURFACE = "NOT_D27_TEST_SURFACE"
    NOT_CURRENT = "NOT_CURRENT"
    UNKNOWN_FAIL_CLOSED = "UNKNOWN_FAIL_CLOSED"


@dataclass(frozen=True, slots=True)
class F5SubfamilyAdjudicationRowV1:
    subfamily: str
    current_owner: str
    classification: EpistemicClassV1
    current_consumer: str
    shadow_entry: str
    baseline_required: str
    gate_authority: str
    gate_type: str
    lifecycle_required: bool
    productive_value_set: int
    verdict: AdjudicationVerdictV1
    wiring_decision: F5WiringDecisionV1
    evidence_refs: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "baseline_required": self.baseline_required,
            "classification": self.classification.value,
            "current_consumer": self.current_consumer,
            "evidence_refs": list(self.evidence_refs),
            "gate_authority": self.gate_authority,
            "gate_type": self.gate_type,
            "lifecycle_required": self.lifecycle_required,
            "productive_value_set": self.productive_value_set,
            "shadow_entry": self.shadow_entry,
            "subfamily": self.subfamily,
            "verdict": self.verdict.value,
            "wiring_decision": self.wiring_decision.value,
            "current_owner": self.current_owner,
        }


def _family_record(gate_id: str):
    for record in optimization_surface_family_records_v1():
        if record.family_gate_id == gate_id:
            return record
    raise KeyError(gate_id)


def _row_f5_fresh(*, productive_value_set: int) -> F5SubfamilyAdjudicationRowV1:
    record = _family_record("F5-FRESH")
    return F5SubfamilyAdjudicationRowV1(
        subfamily="F5-FRESH",
        current_owner=(
            "src/experiments/canonical_f5_fresh_futures_input_freshness_optimizable_surface_v1.py;"
            "src/experiments/f5_fresh_research_candidate_domain_constants_v1.py;"
            "src/ops/productive_pure_stack_numeric_policy_shadow_campaign_v1/"
            "shadow_futures_input_freshness_age_collector_v1.py"
        ),
        classification=EpistemicClassV1.CANONICAL_AUTHORITY,
        current_consumer=f"{SHADOW_CAMPAIGN_ENTRY};{F5_FRESH_COLLECTOR};{ENVELOPE_RESOLVER}",
        shadow_entry=record.test_entry_gate.value,
        baseline_required=(
            "D26_NATIVE_BASELINE_UNRESOLVED_FOR_SHADOW_PACK:"
            "shadow_campaign_uses_stage1_manifest_digest_not_d26_native"
        ),
        gate_authority=(
            "ResearchTestEntryGateV1 matrix (CANONICAL_AUTHORITY label); runtime_enforced=false"
        ),
        gate_type=record.test_entry_gate.value,
        lifecycle_required=True,
        productive_value_set=productive_value_set,
        verdict=AdjudicationVerdictV1.PARTIAL_CURRENT,
        wiring_decision=F5WiringDecisionV1.OWNER_POLICY_REQUIRED,
        evidence_refs=(
            "src/experiments/canonical_optimization_surface_families_pre_test_preparation_v1.py:214-244",
            "src/ops/productive_pure_stack_numeric_policy_shadow_campaign_v1/campaign_runner_v1.py:106",
            "src/ops/productive_pure_stack_numeric_policy_shadow_campaign_v1/"
            "shadow_futures_input_freshness_age_collector_v1.py:27",
            f"config/governance/f5_fresh_futures_input_freshness_optimizable_surface_owner_grant_v1.json",
            f"src/experiments/canonical_f5_fresh_futures_input_freshness_optimizable_surface_v1.py:21 surface_id={F5_FRESH_SURFACE_ID}",
        ),
    )


def _row_f5_surv_cap(
    *,
    subfamily: str,
    owner_decision: str,
    productive_value_set: int,
) -> F5SubfamilyAdjudicationRowV1:
    record = _family_record(subfamily)
    return F5SubfamilyAdjudicationRowV1(
        subfamily=subfamily,
        current_owner=(
            "docs/ops/PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_PROTOCOL_V1.md;"
            "src/experiments/canonical_f5_shadow_per_token_calibration_test_entry_v1.py"
        ),
        classification=EpistemicClassV1.CANONICAL_AUTHORITY,
        current_consumer=f"{SHADOW_CAMPAIGN_ENTRY};shadow_per_token_calibration_entries_v1",
        shadow_entry=record.test_entry_gate.value,
        baseline_required="D26_NATIVE_BASELINE_NOT_BOUND_ON_SHADOW_CALIBRATION_PATH",
        gate_authority="ResearchTestEntryGateV1 matrix; per-token registry; runtime_enforced=false",
        gate_type=record.test_entry_gate.value,
        lifecycle_required=True,
        productive_value_set=productive_value_set,
        verdict=AdjudicationVerdictV1.PARTIAL_CURRENT,
        wiring_decision=F5WiringDecisionV1.OWNER_POLICY_REQUIRED,
        evidence_refs=(
            f"src/experiments/canonical_optimization_surface_families_pre_test_preparation_v1.py:"
            f"{'246-268' if subfamily == 'F5-SURV' else '270-292'}",
            "src/experiments/canonical_f5_shadow_per_token_calibration_test_entry_v1.py:70-73",
            "src/ops/productive_pure_stack_numeric_policy_shadow_campaign_v1/campaign_runner_v1.py:192-205",
            f"owner_decision_id={owner_decision}",
        ),
    )


def build_f5_subfamily_adjudication_matrix_v1() -> tuple[F5SubfamilyAdjudicationRowV1, ...]:
    pset = int(PRODUCTIVE_NUMERIC_VALUES_SET)
    return (
        _row_f5_fresh(productive_value_set=pset),
        _row_f5_surv_cap(subfamily="F5-SURV", owner_decision="D2", productive_value_set=pset),
        _row_f5_surv_cap(subfamily="F5-CAP", owner_decision="D3", productive_value_set=pset),
    )


def build_f5_adjudication_summary_v1(*, repo_root: Path | None = None) -> Mapping[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    rows = build_f5_subfamily_adjudication_matrix_v1()
    registry = build_shadow_calibration_registry_v1()
    fresh = _family_record("F5-FRESH")
    return MappingProxyType(
        {
            "schema_version": SCHEMA_VERSION,
            "workpackage_id": WORKPACKAGE_ID,
            "normative_spec": NORMATIVE_SPEC,
            "decision_config": DECISION_CONFIG,
            "productive_numeric_values_set": int(PRODUCTIVE_NUMERIC_VALUES_SET),
            "shadow_calibration_registry_mode": registry["mode"],
            "f5_fresh_preparation_status": fresh.preparation_status.value,
            "f5_fresh_not_f1_dedupe": fresh.isolation_requirements,
            "subfamily_rows": [r.to_dict() for r in rows],
            "ready_for_bounded_wiring": [
                r.subfamily
                for r in rows
                if r.wiring_decision == F5WiringDecisionV1.READY_FOR_BOUNDED_WIRING
            ],
            "earliest_true_blocker": "f5_shadow_test_entry_gate_not_lifecycle_enforced",
            "implementation_performed": IMPLEMENTATION_PERFORMED,
            "authority_effect": AUTHORITY_EFFECT,
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
            "new_authority_created": NEW_AUTHORITY_CREATED,
            "trading_decision_authority_changed": TRADING_DECISION_AUTHORITY_CHANGED,
            "unknown_conflicting_notes": (
                "D26 native baseline binding policy for shadow evidence pack entry not codified; "
                "OPTIMIZATION_SURFACE_FAMILIES_PRE_TEST_PREPARATION_V1.md §2 vs §3 F5-FRESH envelope "
                "wording tension (INTERPRETATION)."
            ),
            "repo_root_exists": root.is_dir(),
        }
    )


def assert_no_bounded_wiring_without_owner_policy_v1() -> None:
    rows = build_f5_subfamily_adjudication_matrix_v1()
    ready = [r for r in rows if r.wiring_decision == F5WiringDecisionV1.READY_FOR_BOUNDED_WIRING]
    if ready:
        raise ValueError(f"unexpected_ready_for_bounded_wiring:{[r.subfamily for r in ready]}")
    if PRODUCTIVE_NUMERIC_VALUES_SET != 0:
        raise ValueError("productive_numeric_values_set_must_remain_zero")


def prove_d27_f5_shadow_test_entry_subfamily_adjudication_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    required = (
        root / DECISION_CONFIG,
        root / NORMATIVE_SPEC,
        root / "src/governance/d27_f5_shadow_test_entry_authority_subfamily_adjudication_v1.py",
        root
        / "tests/governance/test_d27_f5_shadow_test_entry_authority_subfamily_adjudication_v1.py",
    )
    if not all(p.is_file() for p in required):
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    if not decision.get("f5_subfamily_adjudication_implemented"):
        return False
    if decision.get("f5_bounded_lifecycle_wiring_implemented"):
        return False
    if decision.get("ready_for_bounded_wiring_subfamilies"):
        return False
    try:
        assert_no_bounded_wiring_without_owner_policy_v1()
    except ValueError:
        return False
    rows = build_f5_subfamily_adjudication_matrix_v1()
    if {r.subfamily for r in rows} != set(F5_SUBFAMILY_GATE_IDS):
        return False
    fresh = _family_record("F5-FRESH")
    if fresh.preparation_status != PreparationStatus.TEST_READY_SHADOW_RESEARCH:
        return False
    return True


__all__ = [
    "AUTHORITY_EFFECT",
    "DECISION_CONFIG",
    "AdjudicationVerdictV1",
    "EpistemicClassV1",
    "EXTERNAL_EFFECT_AUTHORIZED",
    "F5WiringDecisionV1",
    "F5_SUBFAMILY_GATE_IDS",
    "F5SubfamilyAdjudicationRowV1",
    "IMPLEMENTATION_PERFORMED",
    "NEW_AUTHORITY_CREATED",
    "NORMATIVE_SPEC",
    "SCHEMA_VERSION",
    "TRADING_DECISION_AUTHORITY_CHANGED",
    "WORKPACKAGE_ID",
    "assert_no_bounded_wiring_without_owner_policy_v1",
    "build_f5_adjudication_summary_v1",
    "build_f5_subfamily_adjudication_matrix_v1",
    "prove_d27_f5_shadow_test_entry_subfamily_adjudication_v1",
]
