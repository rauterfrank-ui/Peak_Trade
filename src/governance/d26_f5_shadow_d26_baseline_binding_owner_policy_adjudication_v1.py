"""D26 × F5 shadow baseline-binding owner-policy adjudication v1 (read-only).

Resolves whether D26 native baseline schema or Stage-1/calibration-protocol digests govern F5
shadow evidence-pack entry. No lifecycle wiring, numeric mutation, or trading authority change.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.governance.d27_research_test_entry_lifecycle_enforcement_v1 import (
    ENFORCED_FAMILY_GATE_IDS,
    D27LifecycleEnforcementScope,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    CALIBRATION_PROTOCOL_REL,
    PRODUCTIVE_NUMERIC_VALUES_SET,
    STAGE1_MANIFEST_REL,
)

SCHEMA_VERSION: Final[str] = "d26_f5_shadow_d26_baseline_binding_owner_policy_adjudication_v1"
WORKPACKAGE_ID: Final[str] = "V32_D26_F5_SHADOW_D26_BASELINE_BINDING_OWNER_POLICY_ADJUDICATION_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/V32_D26_F5_SHADOW_D26_BASELINE_BINDING_OWNER_POLICY_ADJUDICATION_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "v32_d26_f5_shadow_d26_baseline_binding_owner_policy_adjudication_v1_decision_v1.json"
)

D26_DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "v32_d26_platform_unified_native_vs_candidate_baseline_evidence_closure_v1_decision_v1.json"
)
D27_LIFECYCLE_SPEC: Final[str] = (
    "docs/ops/specs/V32_D27_TEST_ENTRY_LIFECYCLE_ENFORCEMENT_FORENSIC_BOUNDED_COMPLETION_V1.md"
)
D27_F5_PREDECESSOR_DECISION: Final[str] = (
    "config/governance/v32_d27_f5_shadow_test_entry_authority_subfamily_adjudication_v1_decision_v1.json"
)

SHADOW_CAMPAIGN_ENTRY: Final[str] = (
    "src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1."
    "campaign_runner_v1.run_shadow_campaign_v1"
)
D26_NATIVE_CLASSIFIER: Final[str] = (
    "src.governance.platform_unified_native_vs_candidate_baseline_evidence_v1."
    "classify_canonical_trading_decision_evidence_v1"
)

F5_SUBFAMILIES: Final[tuple[str, ...]] = ("F5-FRESH", "F5-SURV", "F5-CAP")

AUTHORITY_EFFECT: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
NEW_AUTHORITY_CREATED: Final[bool] = False
TRADING_DECISION_AUTHORITY_CHANGED: Final[bool] = False
IMPLEMENTATION_PERFORMED: Final[bool] = False
LIFECYCLE_ENFORCEMENT_CHANGED: Final[bool] = False


class AdjudicationVerdictV1(str, Enum):
    PROVEN_CURRENT = "PROVEN_CURRENT"
    PARTIAL_CURRENT = "PARTIAL_CURRENT"
    CONFLICTING = "CONFLICTING"
    UNKNOWN = "UNKNOWN"


class EpistemicClassV1(str, Enum):
    CANONICAL_AUTHORITY = "CANONICAL_AUTHORITY"
    ALREADY_ADJUDICATED = "ALREADY_ADJUDICATED"
    NAVIGATION_INDEX_ONLY = "NAVIGATION_INDEX_ONLY"
    INTERPRETATION = "INTERPRETATION"
    HYPOTHESIS = "HYPOTHESIS"
    UNKNOWN = "UNKNOWN"
    CONFLICTING = "CONFLICTING"


class F5ShadowBaselineBindingScopeV1(str, Enum):
    OUT_OF_SCOPE_FOR_D26_NATIVE_SCHEMA = "OUT_OF_SCOPE_FOR_D26_NATIVE_SCHEMA"
    REQUIRED_D26_NATIVE = "REQUIRED_D26_NATIVE"
    UNKNOWN_FAIL_CLOSED = "UNKNOWN_FAIL_CLOSED"


@dataclass(frozen=True, slots=True)
class AuthorityClaimRowV1:
    claim_id: str
    epistemic_class: EpistemicClassV1
    authority_path: str
    symbol_or_field: str
    semantics: str
    applies_to_f5_shadow: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "applies_to_f5_shadow": self.applies_to_f5_shadow,
            "authority_path": self.authority_path,
            "claim_id": self.claim_id,
            "epistemic_class": self.epistemic_class.value,
            "semantics": self.semantics,
            "symbol_or_field": self.symbol_or_field,
        }


def build_authority_claim_matrix_v1() -> tuple[AuthorityClaimRowV1, ...]:
    return (
        AuthorityClaimRowV1(
            claim_id="D26-NATIVE-CLASSIFIER-SCOPE",
            epistemic_class=EpistemicClassV1.CANONICAL_AUTHORITY,
            authority_path="src/governance/platform_unified_native_vs_candidate_baseline_evidence_v1.py",
            symbol_or_field="classify_canonical_trading_decision_evidence_v1",
            semantics=(
                "Read-only influence classification for integrated-replay trading-decision "
                "evidence; AUTHORITY_EFFECT=NONE; not shadow numeric pack schema"
            ),
            applies_to_f5_shadow=False,
        ),
        AuthorityClaimRowV1(
            claim_id="D27-F1F2-D26-ADMISSION",
            epistemic_class=EpistemicClassV1.CANONICAL_AUTHORITY,
            authority_path="src/governance/d27_research_test_entry_lifecycle_enforcement_v1.py",
            symbol_or_field="enforce_d27_test_entry_lifecycle_admission_v1",
            semantics="Fail-closed D26 native baseline required at F1/F2 parameter-influence entry",
            applies_to_f5_shadow=False,
        ),
        AuthorityClaimRowV1(
            claim_id="D27-PATH-P6-F5",
            epistemic_class=EpistemicClassV1.ALREADY_ADJUDICATED,
            authority_path=D27_LIFECYCLE_SPEC,
            symbol_or_field="P6 BASELINE_BOUND",
            semantics="F5 shadow calibration entry owners: baseline_bound=no (explicit matrix row)",
            applies_to_f5_shadow=True,
        ),
        AuthorityClaimRowV1(
            claim_id="D26-NOT-BLOCK-F5",
            epistemic_class=EpistemicClassV1.ALREADY_ADJUDICATED,
            authority_path=D26_DECISION_CONFIG,
            symbol_or_field="d27_blocked_by_d26",
            semantics="false — D26 closure does not mandate F5 shadow native baseline binding",
            applies_to_f5_shadow=True,
        ),
        AuthorityClaimRowV1(
            claim_id="F5-SHADOW-DIGEST-PIN",
            epistemic_class=EpistemicClassV1.CANONICAL_AUTHORITY,
            authority_path=(
                "src/ops/productive_pure_stack_numeric_policy_shadow_campaign_v1/"
                "campaign_runner_v1.py"
            ),
            symbol_or_field="stage1_manifest_digest;calibration_protocol_digest",
            semantics=(
                "Fail-closed digest pin at run_shadow_campaign_v1 entry; "
                f"files {STAGE1_MANIFEST_REL} and {CALIBRATION_PROTOCOL_REL}"
            ),
            applies_to_f5_shadow=True,
        ),
        AuthorityClaimRowV1(
            claim_id="F5-REGISTRY-PROTOCOL-REF",
            epistemic_class=EpistemicClassV1.CANONICAL_AUTHORITY,
            authority_path="src/experiments/canonical_f5_shadow_per_token_calibration_test_entry_v1.py",
            symbol_or_field="calibration_protocol_ref;campaign_manifest_ref",
            semantics="Shadow per-token registry cites protocol/manifest paths (no D26 classifier)",
            applies_to_f5_shadow=True,
        ),
        AuthorityClaimRowV1(
            claim_id="CALIBRATION-PROTOCOL-NAV",
            epistemic_class=EpistemicClassV1.NAVIGATION_INDEX_ONLY,
            authority_path=CALIBRATION_PROTOCOL_REL,
            symbol_or_field="SOLE_TRADING_AUTHORITY",
            semantics=(
                "Points trading SSOT to integrated replay; does not invoke D26 at shadow entry"
            ),
            applies_to_f5_shadow=True,
        ),
        AuthorityClaimRowV1(
            claim_id="D27-F5-PRIOR-UNKNOWN",
            epistemic_class=EpistemicClassV1.ALREADY_ADJUDICATED,
            authority_path=D27_F5_PREDECESSOR_DECISION,
            symbol_or_field="baseline_binding_status",
            semantics="ABSENT_ON_SHADOW_PATHS — superseded by this owner-policy adjudication",
            applies_to_f5_shadow=True,
        ),
    )


def adjudicate_f5_shadow_baseline_binding_policy_v1() -> Mapping[str, Any]:
    claims = build_authority_claim_matrix_v1()
    f5_digest_authority = any(
        c.claim_id == "F5-SHADOW-DIGEST-PIN"
        and c.epistemic_class == EpistemicClassV1.CANONICAL_AUTHORITY
        for c in claims
    )
    d26_on_f5_required = any(
        c.applies_to_f5_shadow
        and c.claim_id == "D27-F1F2-D26-ADMISSION"
        and "required" in c.semantics.lower()
        for c in claims
    )
    p6_no_baseline = any(c.claim_id == "D27-PATH-P6-F5" for c in claims)

    if d26_on_f5_required and p6_no_baseline:
        conflict_status = "CONFLICTING"
        adjudication_result = AdjudicationVerdictV1.CONFLICTING
        f5_scope = F5ShadowBaselineBindingScopeV1.UNKNOWN_FAIL_CLOSED
    elif f5_digest_authority and p6_no_baseline and not d26_on_f5_required:
        conflict_status = "RESOLVED"
        adjudication_result = AdjudicationVerdictV1.PROVEN_CURRENT
        f5_scope = F5ShadowBaselineBindingScopeV1.OUT_OF_SCOPE_FOR_D26_NATIVE_SCHEMA
    else:
        conflict_status = "UNKNOWN"
        adjudication_result = AdjudicationVerdictV1.UNKNOWN
        f5_scope = F5ShadowBaselineBindingScopeV1.UNKNOWN_FAIL_CLOSED

    return MappingProxyType(
        {
            "schema_version": SCHEMA_VERSION,
            "workpackage_id": WORKPACKAGE_ID,
            "authority_claims": [c.to_dict() for c in claims],
            "d26_native_baseline_authority_status": AdjudicationVerdictV1.PROVEN_CURRENT.value,
            "stage1_entry_authority_status": AdjudicationVerdictV1.PROVEN_CURRENT.value,
            "calibration_protocol_authority_status": AdjudicationVerdictV1.PROVEN_CURRENT.value,
            "f5_baseline_binding_policy_status": (
                "PROVEN_CURRENT_DOMAIN_SEPARATED"
                if adjudication_result == AdjudicationVerdictV1.PROVEN_CURRENT
                else adjudication_result.value
            ),
            "conflict_status": conflict_status,
            "adjudication_result": adjudication_result.value,
            "d26_native_on_f5_shadow_scope": f5_scope.value,
            "f5_shadow_pack_entry_authority": (
                "STAGE1_MANIFEST_DIGEST_PLUS_CALIBRATION_PROTOCOL_DIGEST"
                if adjudication_result == AdjudicationVerdictV1.PROVEN_CURRENT
                else "UNKNOWN"
            ),
            "baseline_before_parameter_influence": True,
            "baseline_evidence_passive_only": True,
            "d27_enforced_families": list(ENFORCED_FAMILY_GATE_IDS),
            "d27_enforcement_scope_excludes_f5": (
                D27LifecycleEnforcementScope.TEST_READY_F1_F2_PARAMETER_INFLUENCE.value
            ),
            "f5_subfamilies": list(F5_SUBFAMILIES),
            "productive_numeric_values_set": int(PRODUCTIVE_NUMERIC_VALUES_SET),
            "shadow_campaign_entry": SHADOW_CAMPAIGN_ENTRY,
            "d26_native_classifier": D26_NATIVE_CLASSIFIER,
            "earliest_true_blocker": "f5_shadow_test_entry_gate_not_lifecycle_enforced",
            "implementation_performed": IMPLEMENTATION_PERFORMED,
            "lifecycle_enforcement_changed": LIFECYCLE_ENFORCEMENT_CHANGED,
            "authority_effect": AUTHORITY_EFFECT,
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
            "new_authority_created": NEW_AUTHORITY_CREATED,
            "trading_decision_authority_changed": TRADING_DECISION_AUTHORITY_CHANGED,
        }
    )


def assert_adjudication_invariants_v1() -> None:
    policy = adjudicate_f5_shadow_baseline_binding_policy_v1()
    if policy["adjudication_result"] != AdjudicationVerdictV1.PROVEN_CURRENT.value:
        raise ValueError(f"adjudication_not_proven_current:{policy['adjudication_result']}")
    if policy["conflict_status"] != "RESOLVED":
        raise ValueError(f"conflict_not_resolved:{policy['conflict_status']}")
    if int(policy["productive_numeric_values_set"]) != 0:
        raise ValueError("productive_numeric_values_set_must_remain_zero")
    if policy["d26_native_on_f5_shadow_scope"] != (
        F5ShadowBaselineBindingScopeV1.OUT_OF_SCOPE_FOR_D26_NATIVE_SCHEMA.value
    ):
        raise ValueError("d26_native_on_f5_shadow_scope_mismatch")


def prove_d26_f5_shadow_d26_baseline_binding_owner_policy_adjudication_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    required = (
        root / DECISION_CONFIG,
        root / NORMATIVE_SPEC,
        root / "src/governance/d26_f5_shadow_d26_baseline_binding_owner_policy_adjudication_v1.py",
        root / "tests/governance/"
        "test_d26_f5_shadow_d26_baseline_binding_owner_policy_adjudication_v1.py",
        root / STAGE1_MANIFEST_REL,
        root / CALIBRATION_PROTOCOL_REL,
    )
    if not all(p.is_file() for p in required):
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    if not decision.get("owner_policy_implemented"):
        return False
    if decision.get("adjudication_result") != "PROVEN_CURRENT":
        return False
    if decision.get("conflict_status") != "RESOLVED":
        return False
    if decision.get("f5_bounded_lifecycle_wiring_implemented"):
        return False
    if decision.get("lifecycle_enforcement_changed"):
        return False
    if decision.get("productive_numeric_values_set_current") != 0:
        return False
    try:
        assert_adjudication_invariants_v1()
    except ValueError:
        return False
    return True


__all__ = [
    "AUTHORITY_EFFECT",
    "DECISION_CONFIG",
    "AdjudicationVerdictV1",
    "AuthorityClaimRowV1",
    "EpistemicClassV1",
    "EXTERNAL_EFFECT_AUTHORIZED",
    "F5ShadowBaselineBindingScopeV1",
    "F5_SUBFAMILIES",
    "IMPLEMENTATION_PERFORMED",
    "LIFECYCLE_ENFORCEMENT_CHANGED",
    "NEW_AUTHORITY_CREATED",
    "NORMATIVE_SPEC",
    "SCHEMA_VERSION",
    "TRADING_DECISION_AUTHORITY_CHANGED",
    "WORKPACKAGE_ID",
    "adjudicate_f5_shadow_baseline_binding_policy_v1",
    "assert_adjudication_invariants_v1",
    "build_authority_claim_matrix_v1",
    "prove_d26_f5_shadow_d26_baseline_binding_owner_policy_adjudication_v1",
]
