"""D26 × F5 shadow baseline-binding owner-policy adjudication tests (read-only)."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.d26_f5_shadow_d26_baseline_binding_owner_policy_adjudication_v1 import (
    DECISION_CONFIG,
    AdjudicationVerdictV1,
    EpistemicClassV1,
    F5ShadowBaselineBindingScopeV1,
    IMPLEMENTATION_PERFORMED,
    adjudicate_f5_shadow_baseline_binding_policy_v1,
    build_authority_claim_matrix_v1,
    prove_d26_f5_shadow_d26_baseline_binding_owner_policy_adjudication_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_closure_proof_and_decision_json() -> None:
    assert prove_d26_f5_shadow_d26_baseline_binding_owner_policy_adjudication_v1(
        repo_root=REPO_ROOT
    )
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["owner_policy_implemented"] is True
    assert decision["adjudication_result"] == "PROVEN_CURRENT"
    assert decision["conflict_status"] == "RESOLVED"
    assert decision["f5_bounded_lifecycle_wiring_implemented"] is False
    assert decision["lifecycle_enforcement_changed"] is False
    assert decision["productive_numeric_values_set_current"] == 0
    assert decision["new_authority_created"] is False
    assert decision["external_effect_authorized"] is False


def test_policy_domain_separated_not_conflicting() -> None:
    policy = adjudicate_f5_shadow_baseline_binding_policy_v1()
    assert policy["adjudication_result"] == AdjudicationVerdictV1.PROVEN_CURRENT.value
    assert policy["conflict_status"] == "RESOLVED"
    assert (
        policy["d26_native_on_f5_shadow_scope"]
        == F5ShadowBaselineBindingScopeV1.OUT_OF_SCOPE_FOR_D26_NATIVE_SCHEMA.value
    )
    assert policy["f5_shadow_pack_entry_authority"].startswith("STAGE1_MANIFEST_DIGEST")
    assert policy["productive_numeric_values_set"] == PRODUCTIVE_NUMERIC_VALUES_SET == 0
    assert policy["implementation_performed"] is IMPLEMENTATION_PERFORMED is False


def test_authority_claim_matrix_covers_digest_and_d27_p6() -> None:
    claims = build_authority_claim_matrix_v1()
    claim_ids = {c.claim_id for c in claims}
    assert "F5-SHADOW-DIGEST-PIN" in claim_ids
    assert "D27-PATH-P6-F5" in claim_ids
    digest = next(c for c in claims if c.claim_id == "F5-SHADOW-DIGEST-PIN")
    assert digest.epistemic_class == EpistemicClassV1.CANONICAL_AUTHORITY
    assert digest.applies_to_f5_shadow is True
    p6 = next(c for c in claims if c.claim_id == "D27-PATH-P6-F5")
    assert "baseline_bound=no" in p6.semantics.lower()
