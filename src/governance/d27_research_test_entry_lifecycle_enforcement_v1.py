"""D27 test-entry lifecycle enforcement v1 — compose pre-test gates + D26 native baseline admission.

Fail-closed admission before TEST_READY parameter-influence research executors (F1/F2).
Does not authorize promotion, productive apply, external effect, or new trading authority.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final, Mapping

from src.governance.platform_unified_native_vs_candidate_baseline_evidence_v1 import (
    InfluenceClassificationV1,
    SCHEMA_VERSION as D26_SCHEMA_VERSION,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

if TYPE_CHECKING:
    from src.experiments.canonical_optimization_surface_families_pre_test_preparation_v1 import (
        OptimizationSurfaceFamilyRecordV1,
    )

SCHEMA_VERSION: Final[str] = "d27_research_test_entry_lifecycle_enforcement_v1"
WORKPACKAGE_ID: Final[str] = (
    "V32_D27_TEST_ENTRY_LIFECYCLE_ENFORCEMENT_FORENSIC_BOUNDED_COMPLETION_V1"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/V32_D27_TEST_ENTRY_LIFECYCLE_ENFORCEMENT_FORENSIC_BOUNDED_COMPLETION_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "v32_d27_test_entry_lifecycle_enforcement_forensic_bounded_completion_v1_decision_v1.json"
)

PRE_TEST_GATE_OWNER: Final[str] = (
    "src.experiments.canonical_optimization_surface_families_pre_test_preparation_v1."
    "ResearchTestEntryGateV1"
)
D26_NATIVE_CLASSIFIER: Final[str] = (
    "src.governance.platform_unified_native_vs_candidate_baseline_evidence_v1."
    "classify_canonical_trading_decision_evidence_v1"
)

F1_FAMILY_GATE_ID: Final[str] = "F1"
F2_FAMILY_GATE_ID: Final[str] = "F2"
F1_TEST_ENTRY_GATE: Final[str] = (
    "PREREGISTERED_VOLATILITY_MAX_AGE_PARAMETER_RESEARCH_EXECUTION_V1"
)
F2_TEST_ENTRY_GATE: Final[str] = (
    "DETERMINISTIC_F2_COST_GRID_IDENTITY_REPLAY_THEN_BOUNDED_SENSITIVITY_OOS_V1"
)

ENFORCED_FAMILY_GATE_IDS: Final[tuple[str, ...]] = (F1_FAMILY_GATE_ID, F2_FAMILY_GATE_ID)
F1_EXECUTOR_OWNER: Final[str] = (
    "research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.runner_v1."
    "run_max_age_parameter_research_execution_v1"
)
F2_EXECUTOR_OWNER: Final[str] = (
    "src.experiments.canonical_f2_research_backtest_cost_grid_research_execution_v1."
    "run_f2_research_backtest_cost_grid_offline_v1"
)

AUTHORITY_EFFECT: Final[str] = "NONE"
RUNTIME_EFFECT: Final[str] = "RESEARCH_ENTRY_FAIL_CLOSED_GATE"
PROMOTION_AUTHORITY: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
TRADING_DECISION_AUTHORITY_CHANGED: Final[bool] = False
NEW_AUTHORITY_CREATED: Final[bool] = False

EARLIEST_GAP_AFTER_F1_F2_ENFORCED: Final[str] = "f5_shadow_test_entry_gate_not_lifecycle_enforced"


class D27LifecycleEnforcementScope(str, Enum):
    TEST_READY_F1_F2_PARAMETER_INFLUENCE = "TEST_READY_F1_F2_PARAMETER_INFLUENCE"


class D27ResearchTestEntryLifecycleError(ValueError):
    """Fail-closed D27 admission error."""


@dataclass(frozen=True, slots=True)
class D27TestEntryLifecycleAdmissionV1:
    schema_version: str
    family_gate_id: str
    test_entry_gate: str
    preparation_status: str
    baseline_reference_identity: str
    native_baseline_record_id: str
    admission_digest: str
    enforcement_scope: D27LifecycleEnforcementScope
    authority_effect: str
    runtime_effect: str
    promotion_authority: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "admission_digest": self.admission_digest,
            "authority_effect": self.authority_effect,
            "baseline_reference_identity": self.baseline_reference_identity,
            "enforcement_scope": self.enforcement_scope.value,
            "family_gate_id": self.family_gate_id,
            "native_baseline_record_id": self.native_baseline_record_id,
            "preparation_status": self.preparation_status,
            "promotion_authority": self.promotion_authority,
            "runtime_effect": self.runtime_effect,
            "schema_version": self.schema_version,
            "test_entry_gate": self.test_entry_gate,
        }


def family_record_by_gate_id_v1(family_gate_id: str) -> OptimizationSurfaceFamilyRecordV1:
    from src.experiments.canonical_optimization_surface_families_pre_test_preparation_v1 import (
        optimization_surface_family_records_v1,
    )

    for record in optimization_surface_family_records_v1():
        if record.family_gate_id == family_gate_id:
            return record
    raise D27ResearchTestEntryLifecycleError(f"FAMILY_GATE_UNKNOWN:{family_gate_id}")


def parse_native_baseline_evidence_payload_v1(
    payload: Mapping[str, Any],
) -> Mapping[str, Any]:
    if not payload:
        raise D27ResearchTestEntryLifecycleError("NATIVE_BASELINE_EVIDENCE_REQUIRED")
    schema = str(payload.get("schema_version") or "")
    if schema != D26_SCHEMA_VERSION:
        raise D27ResearchTestEntryLifecycleError("NATIVE_BASELINE_SCHEMA_MISMATCH")
    classification = str(payload.get("influence_classification") or "")
    if classification != InfluenceClassificationV1.NATIVE_BASELINE.value:
        raise D27ResearchTestEntryLifecycleError("NATIVE_BASELINE_CLASSIFICATION_REQUIRED")
    fail_reasons = payload.get("fail_closed_reasons") or []
    if fail_reasons:
        raise D27ResearchTestEntryLifecycleError(
            f"NATIVE_BASELINE_FAIL_CLOSED:{','.join(map(str, fail_reasons))}"
        )
    if payload.get("candidate_identity") is not None:
        raise D27ResearchTestEntryLifecycleError(
            "NATIVE_BASELINE_MUST_NOT_CARRY_CANDIDATE_IDENTITY"
        )
    baseline_ref = str(payload.get("baseline_reference_identity") or "")
    if not is_valid_sha256_hex(baseline_ref):
        raise D27ResearchTestEntryLifecycleError("NATIVE_BASELINE_REFERENCE_IDENTITY_INVALID")
    record_id = str(payload.get("record_id") or "")
    if not record_id:
        raise D27ResearchTestEntryLifecycleError("NATIVE_BASELINE_RECORD_ID_MISSING")
    return MappingProxyType(dict(payload))


def enforce_d27_test_entry_lifecycle_admission_v1(
    *,
    family_gate_id: str,
    declared_test_entry_gate: str,
    native_baseline_evidence: Mapping[str, Any],
    enforcement_scope: D27LifecycleEnforcementScope = (
        D27LifecycleEnforcementScope.TEST_READY_F1_F2_PARAMETER_INFLUENCE
    ),
) -> D27TestEntryLifecycleAdmissionV1:
    """Single entry admission: matrix gate + TEST_READY + D26 native baseline (fail-closed)."""
    from src.experiments.canonical_optimization_surface_families_pre_test_preparation_v1 import (
        PreparationStatus,
        ResearchTestEntryGateV1,
    )

    record = family_record_by_gate_id_v1(family_gate_id)
    if record.preparation_status != PreparationStatus.TEST_READY:
        raise D27ResearchTestEntryLifecycleError(
            f"FAMILY_NOT_TEST_READY:{family_gate_id}:{record.preparation_status.value}"
        )
    expected_gate = record.test_entry_gate.value
    if str(declared_test_entry_gate) != expected_gate:
        raise D27ResearchTestEntryLifecycleError(
            f"TEST_ENTRY_GATE_MISMATCH:expected={expected_gate} declared={declared_test_entry_gate}"
        )
    if record.test_entry_gate == ResearchTestEntryGateV1.UNKNOWN_FAIL_CLOSED:
        raise D27ResearchTestEntryLifecycleError("TEST_ENTRY_GATE_UNKNOWN_FAIL_CLOSED")

    native = parse_native_baseline_evidence_payload_v1(native_baseline_evidence)
    baseline_ref = str(native["baseline_reference_identity"])

    body = {
        "baseline_reference_identity": baseline_ref,
        "digest_domain": f"{SCHEMA_VERSION}.admission",
        "enforcement_scope": enforcement_scope.value,
        "family_gate_id": family_gate_id,
        "native_baseline_record_id": str(native["record_id"]),
        "preparation_status": record.preparation_status.value,
        "test_entry_gate": expected_gate,
    }
    admission_digest = compute_content_sha256(body)

    return D27TestEntryLifecycleAdmissionV1(
        schema_version=SCHEMA_VERSION,
        family_gate_id=family_gate_id,
        test_entry_gate=expected_gate,
        preparation_status=record.preparation_status.value,
        baseline_reference_identity=baseline_ref,
        native_baseline_record_id=str(native["record_id"]),
        admission_digest=admission_digest,
        enforcement_scope=enforcement_scope,
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
        promotion_authority=PROMOTION_AUTHORITY,
    )


def enforce_d27_f1_test_entry_lifecycle_v1(
    *,
    native_baseline_evidence: Mapping[str, Any],
) -> D27TestEntryLifecycleAdmissionV1:
    return enforce_d27_test_entry_lifecycle_admission_v1(
        family_gate_id=F1_FAMILY_GATE_ID,
        declared_test_entry_gate=F1_TEST_ENTRY_GATE,
        native_baseline_evidence=native_baseline_evidence,
    )


def enforce_d27_f2_test_entry_lifecycle_v1(
    *,
    native_baseline_evidence: Mapping[str, Any],
) -> D27TestEntryLifecycleAdmissionV1:
    return enforce_d27_test_entry_lifecycle_admission_v1(
        family_gate_id=F2_FAMILY_GATE_ID,
        declared_test_entry_gate=F2_TEST_ENTRY_GATE,
        native_baseline_evidence=native_baseline_evidence,
    )


def bind_native_baseline_evidence_from_classification_dict_v1(
    classification_record: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Normalize an already-classified D26 record dict for D27 admission input."""
    return parse_native_baseline_evidence_payload_v1(classification_record)


def prove_d27_f1_f2_test_entry_lifecycle_enforcement_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    required = (
        root / DECISION_CONFIG,
        root / NORMATIVE_SPEC,
        root / "src/governance/d27_research_test_entry_lifecycle_enforcement_v1.py",
        root
        / "src/research/canonical_volatility_numeric_max_age_parameter_research_execution_v1"
        / "runner_v1.py",
        root / "src/experiments/canonical_f2_research_backtest_cost_grid_research_execution_v1.py",
        root / "tests/governance/test_d27_research_test_entry_lifecycle_enforcement_v1.py",
    )
    if not all(path.is_file() for path in required):
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    if not decision.get("d27_f1_f2_lifecycle_enforcement_implemented"):
        return False
    runner_text = required[3].read_text(encoding="utf-8")
    f2_text = required[4].read_text(encoding="utf-8")
    if "enforce_d27_f1_test_entry_lifecycle_v1" not in runner_text:
        return False
    if "enforce_d27_f2_test_entry_lifecycle_v1" not in f2_text:
        return False
    return decision.get("enforced_family_gate_ids") == list(ENFORCED_FAMILY_GATE_IDS)


__all__ = [
    "AUTHORITY_EFFECT",
    "D26_NATIVE_CLASSIFIER",
    "DECISION_CONFIG",
    "D27LifecycleEnforcementScope",
    "D27ResearchTestEntryLifecycleError",
    "D27TestEntryLifecycleAdmissionV1",
    "EARLIEST_GAP_AFTER_F1_F2_ENFORCED",
    "ENFORCED_FAMILY_GATE_IDS",
    "EXTERNAL_EFFECT_AUTHORIZED",
    "F1_EXECUTOR_OWNER",
    "F1_FAMILY_GATE_ID",
    "F1_TEST_ENTRY_GATE",
    "F2_EXECUTOR_OWNER",
    "F2_FAMILY_GATE_ID",
    "F2_TEST_ENTRY_GATE",
    "NEW_AUTHORITY_CREATED",
    "NORMATIVE_SPEC",
    "PRE_TEST_GATE_OWNER",
    "PROMOTION_AUTHORITY",
    "RUNTIME_EFFECT",
    "SCHEMA_VERSION",
    "TRADING_DECISION_AUTHORITY_CHANGED",
    "WORKPACKAGE_ID",
    "bind_native_baseline_evidence_from_classification_dict_v1",
    "enforce_d27_f1_test_entry_lifecycle_v1",
    "enforce_d27_f2_test_entry_lifecycle_v1",
    "enforce_d27_test_entry_lifecycle_admission_v1",
    "family_record_by_gate_id_v1",
    "parse_native_baseline_evidence_payload_v1",
    "prove_d27_f1_f2_test_entry_lifecycle_enforcement_v1",
]
