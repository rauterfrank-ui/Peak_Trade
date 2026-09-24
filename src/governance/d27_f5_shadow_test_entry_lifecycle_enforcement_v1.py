"""D27 F5 shadow/test-entry lifecycle enforcement v1 — digest conjunction fail-closed admission.

Enforces pre-test TEST_ENTRY_GATE matrix rows plus Stage-1 manifest and calibration-protocol
digest pins at F5 shadow campaign entry. D26 native baseline is explicitly out of scope.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.governance.d26_f5_shadow_d26_baseline_binding_owner_policy_adjudication_v1 import (
    F5ShadowBaselineBindingScopeV1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    CALIBRATION_PROTOCOL_REL,
    PRODUCTIVE_NUMERIC_VALUES_SET,
    STAGE1_MANIFEST_REL,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.reproducibility_v1 import (
    sha256_file,
)

SCHEMA_VERSION: Final[str] = "d27_f5_shadow_test_entry_lifecycle_enforcement_v1"
WORKPACKAGE_ID: Final[str] = "V32_D27_F5_SHADOW_TEST_ENTRY_LIFECYCLE_ENFORCEMENT_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/V32_D27_F5_SHADOW_TEST_ENTRY_LIFECYCLE_ENFORCEMENT_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/v32_d27_f5_shadow_test_entry_lifecycle_enforcement_v1_decision_v1.json"
)
D26_F5_POLICY_DECISION: Final[str] = (
    "config/governance/"
    "v32_d26_f5_shadow_d26_baseline_binding_owner_policy_adjudication_v1_decision_v1.json"
)

PRE_TEST_GATE_OWNER: Final[str] = (
    "src.experiments.canonical_optimization_surface_families_pre_test_preparation_v1."
    "ResearchTestEntryGateV1"
)
SHADOW_CAMPAIGN_ENTRY: Final[str] = (
    "src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1."
    "campaign_runner_v1.run_shadow_campaign_v1"
)

F5_FRESH_FAMILY_GATE_ID: Final[str] = "F5-FRESH"
F5_FRESH_TEST_ENTRY_GATE: Final[str] = "SHADOW_PURE_STACK_NUMERIC_EVIDENCE_PACK_VALIDATION_V1"

ENFORCED_SHADOW_ENTRY_OWNERS: Final[tuple[str, ...]] = (SHADOW_CAMPAIGN_ENTRY,)

AUTHORITY_EFFECT: Final[str] = "NONE"
RUNTIME_EFFECT: Final[str] = "F5_SHADOW_ENTRY_FAIL_CLOSED_GATE"
PROMOTION_AUTHORITY: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
TRADING_DECISION_AUTHORITY_CHANGED: Final[bool] = False
NEW_AUTHORITY_CREATED: Final[bool] = False
D26_NATIVE_BASELINE_ON_F5: Final[str] = (
    F5ShadowBaselineBindingScopeV1.OUT_OF_SCOPE_FOR_D26_NATIVE_SCHEMA.value
)


class D27F5ShadowTestEntryLifecycleError(ValueError):
    """Fail-closed F5 shadow test-entry admission error."""


class D27F5ShadowLifecycleEnforcementScope(str, Enum):
    TEST_READY_F5_FRESH_SHADOW_CAMPAIGN = "TEST_READY_F5_FRESH_SHADOW_CAMPAIGN"


@dataclass(frozen=True, slots=True)
class D27F5ShadowTestEntryLifecycleAdmissionV1:
    schema_version: str
    family_gate_id: str
    test_entry_gate: str
    preparation_status: str
    stage1_manifest_digest: str
    calibration_protocol_digest: str
    stage1_manifest_rel: str
    calibration_protocol_rel: str
    d26_native_baseline_scope: str
    admission_digest: str
    enforcement_scope: D27F5ShadowLifecycleEnforcementScope
    authority_effect: str
    runtime_effect: str
    promotion_authority: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "admission_digest": self.admission_digest,
            "authority_effect": self.authority_effect,
            "calibration_protocol_digest": self.calibration_protocol_digest,
            "calibration_protocol_rel": self.calibration_protocol_rel,
            "d26_native_baseline_scope": self.d26_native_baseline_scope,
            "enforcement_scope": self.enforcement_scope.value,
            "family_gate_id": self.family_gate_id,
            "preparation_status": self.preparation_status,
            "promotion_authority": self.promotion_authority,
            "runtime_effect": self.runtime_effect,
            "schema_version": self.schema_version,
            "stage1_manifest_digest": self.stage1_manifest_digest,
            "stage1_manifest_rel": self.stage1_manifest_rel,
            "test_entry_gate": self.test_entry_gate,
        }


def _family_record_f5_fresh_v1():
    from src.experiments.canonical_optimization_surface_families_pre_test_preparation_v1 import (
        PreparationStatus,
        optimization_surface_family_records_v1,
    )

    for record in optimization_surface_family_records_v1():
        if record.family_gate_id == F5_FRESH_FAMILY_GATE_ID:
            if record.preparation_status != PreparationStatus.TEST_READY_SHADOW_RESEARCH:
                raise D27F5ShadowTestEntryLifecycleError(
                    f"F5_FRESH_NOT_TEST_READY:{record.preparation_status.value}"
                )
            return record
    raise D27F5ShadowTestEntryLifecycleError("F5_FRESH_FAMILY_RECORD_MISSING")


def _resolve_digest_or_deny(*, repo_root: Path, rel_path: str, label: str) -> str:
    path = repo_root / rel_path
    if not path.is_file():
        raise D27F5ShadowTestEntryLifecycleError(f"{label}_SOURCE_MISSING:{rel_path}")
    return sha256_file(path)


def enforce_d27_f5_shadow_test_entry_lifecycle_admission_v1(
    *,
    family_gate_id: str,
    declared_test_entry_gate: str,
    repo_root: Path,
    declared_stage1_manifest_digest: str,
    declared_calibration_protocol_digest: str,
    enforcement_scope: D27F5ShadowLifecycleEnforcementScope = (
        D27F5ShadowLifecycleEnforcementScope.TEST_READY_F5_FRESH_SHADOW_CAMPAIGN
    ),
) -> D27F5ShadowTestEntryLifecycleAdmissionV1:
    """Matrix gate + TEST_READY + Stage-1/calibration digest conjunction (fail-closed)."""
    if family_gate_id != F5_FRESH_FAMILY_GATE_ID:
        raise D27F5ShadowTestEntryLifecycleError(f"FAMILY_GATE_NOT_F5_SHADOW:{family_gate_id}")

    record = _family_record_f5_fresh_v1()
    expected_gate = record.test_entry_gate.value
    if str(declared_test_entry_gate) != expected_gate:
        raise D27F5ShadowTestEntryLifecycleError(
            f"TEST_ENTRY_GATE_MISMATCH:expected={expected_gate} declared={declared_test_entry_gate}"
        )

    if not is_valid_sha256_hex(str(declared_stage1_manifest_digest or "")):
        raise D27F5ShadowTestEntryLifecycleError("STAGE1_MANIFEST_DIGEST_INVALID")
    if not is_valid_sha256_hex(str(declared_calibration_protocol_digest or "")):
        raise D27F5ShadowTestEntryLifecycleError("CALIBRATION_PROTOCOL_DIGEST_INVALID")

    stage1_actual = _resolve_digest_or_deny(
        repo_root=repo_root, rel_path=STAGE1_MANIFEST_REL, label="STAGE1_MANIFEST"
    )
    protocol_actual = _resolve_digest_or_deny(
        repo_root=repo_root, rel_path=CALIBRATION_PROTOCOL_REL, label="CALIBRATION_PROTOCOL"
    )

    if declared_stage1_manifest_digest != stage1_actual:
        raise D27F5ShadowTestEntryLifecycleError("STAGE1_MANIFEST_DIGEST_MISMATCH")
    if declared_calibration_protocol_digest != protocol_actual:
        raise D27F5ShadowTestEntryLifecycleError("CALIBRATION_PROTOCOL_DIGEST_MISMATCH")

    body = {
        "calibration_protocol_digest": protocol_actual,
        "calibration_protocol_rel": CALIBRATION_PROTOCOL_REL,
        "d26_native_baseline_scope": D26_NATIVE_BASELINE_ON_F5,
        "digest_domain": f"{SCHEMA_VERSION}.admission",
        "enforcement_scope": enforcement_scope.value,
        "family_gate_id": family_gate_id,
        "preparation_status": record.preparation_status.value,
        "stage1_manifest_digest": stage1_actual,
        "stage1_manifest_rel": STAGE1_MANIFEST_REL,
        "test_entry_gate": expected_gate,
    }
    admission_digest = compute_content_sha256(body)

    return D27F5ShadowTestEntryLifecycleAdmissionV1(
        schema_version=SCHEMA_VERSION,
        family_gate_id=family_gate_id,
        test_entry_gate=expected_gate,
        preparation_status=record.preparation_status.value,
        stage1_manifest_digest=stage1_actual,
        calibration_protocol_digest=protocol_actual,
        stage1_manifest_rel=STAGE1_MANIFEST_REL,
        calibration_protocol_rel=CALIBRATION_PROTOCOL_REL,
        d26_native_baseline_scope=D26_NATIVE_BASELINE_ON_F5,
        admission_digest=admission_digest,
        enforcement_scope=enforcement_scope,
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
        promotion_authority=PROMOTION_AUTHORITY,
    )


def enforce_d27_f5_fresh_shadow_campaign_test_entry_lifecycle_v1(
    *,
    repo_root: Path,
    declared_stage1_manifest_digest: str,
    declared_calibration_protocol_digest: str,
) -> D27F5ShadowTestEntryLifecycleAdmissionV1:
    return enforce_d27_f5_shadow_test_entry_lifecycle_admission_v1(
        family_gate_id=F5_FRESH_FAMILY_GATE_ID,
        declared_test_entry_gate=F5_FRESH_TEST_ENTRY_GATE,
        repo_root=repo_root,
        declared_stage1_manifest_digest=declared_stage1_manifest_digest,
        declared_calibration_protocol_digest=declared_calibration_protocol_digest,
    )


def prove_d27_f5_shadow_test_entry_lifecycle_enforcement_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    required = (
        root / DECISION_CONFIG,
        root / NORMATIVE_SPEC,
        root / D26_F5_POLICY_DECISION,
        root / "src/governance/d27_f5_shadow_test_entry_lifecycle_enforcement_v1.py",
        root
        / "src/ops/productive_pure_stack_numeric_policy_shadow_campaign_v1/campaign_runner_v1.py",
        root / "tests/governance/test_d27_f5_shadow_test_entry_lifecycle_enforcement_v1.py",
    )
    if not all(p.is_file() for p in required):
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    if not decision.get("f5_shadow_lifecycle_enforcement_implemented"):
        return False
    if decision.get("d26_native_baseline_required_on_f5"):
        return False
    if int(decision.get("productive_numeric_values_set_current", -1)) != 0:
        return False
    runner_text = required[4].read_text(encoding="utf-8")
    if "enforce_d27_f5_fresh_shadow_campaign_test_entry_lifecycle_v1" not in runner_text:
        return False
    if PRODUCTIVE_NUMERIC_VALUES_SET != 0:
        return False
    return True


def build_f5_shadow_lifecycle_enforcement_summary_v1() -> Mapping[str, Any]:
    return MappingProxyType(
        {
            "schema_version": SCHEMA_VERSION,
            "workpackage_id": WORKPACKAGE_ID,
            "enforced_shadow_entry_owners": list(ENFORCED_SHADOW_ENTRY_OWNERS),
            "f5_fresh_test_entry_gate": F5_FRESH_TEST_ENTRY_GATE,
            "d26_native_baseline_scope": D26_NATIVE_BASELINE_ON_F5,
            "entry_conjunction": (
                "STAGE1_MANIFEST_DIGEST_AND_CALIBRATION_PROTOCOL_DIGEST_AND_MATRIX_TEST_ENTRY_GATE"
            ),
            "productive_numeric_values_set": int(PRODUCTIVE_NUMERIC_VALUES_SET),
            "promotion_authority": PROMOTION_AUTHORITY,
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
            "new_authority_created": NEW_AUTHORITY_CREATED,
            "trading_decision_authority_changed": TRADING_DECISION_AUTHORITY_CHANGED,
        }
    )


__all__ = [
    "AUTHORITY_EFFECT",
    "DECISION_CONFIG",
    "D26_NATIVE_BASELINE_ON_F5",
    "D27F5ShadowLifecycleEnforcementScope",
    "D27F5ShadowTestEntryLifecycleAdmissionV1",
    "D27F5ShadowTestEntryLifecycleError",
    "ENFORCED_SHADOW_ENTRY_OWNERS",
    "EXTERNAL_EFFECT_AUTHORIZED",
    "F5_FRESH_FAMILY_GATE_ID",
    "F5_FRESH_TEST_ENTRY_GATE",
    "NEW_AUTHORITY_CREATED",
    "NORMATIVE_SPEC",
    "PRE_TEST_GATE_OWNER",
    "PROMOTION_AUTHORITY",
    "RUNTIME_EFFECT",
    "SCHEMA_VERSION",
    "SHADOW_CAMPAIGN_ENTRY",
    "TRADING_DECISION_AUTHORITY_CHANGED",
    "WORKPACKAGE_ID",
    "build_f5_shadow_lifecycle_enforcement_summary_v1",
    "enforce_d27_f5_fresh_shadow_campaign_test_entry_lifecycle_v1",
    "enforce_d27_f5_shadow_test_entry_lifecycle_admission_v1",
    "prove_d27_f5_shadow_test_entry_lifecycle_enforcement_v1",
]
