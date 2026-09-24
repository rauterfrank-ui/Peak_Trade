"""D27 F5 shadow subfamily adjudication tests (read-only; no lifecycle wiring)."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.d27_f5_shadow_test_entry_authority_subfamily_adjudication_v1 import (
    DECISION_CONFIG,
    AdjudicationVerdictV1,
    F5WiringDecisionV1,
    F5_SUBFAMILY_GATE_IDS,
    IMPLEMENTATION_PERFORMED,
    build_f5_adjudication_summary_v1,
    build_f5_subfamily_adjudication_matrix_v1,
    prove_d27_f5_shadow_test_entry_subfamily_adjudication_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_f5_adjudication_closure_proof() -> None:
    assert prove_d27_f5_shadow_test_entry_subfamily_adjudication_v1(repo_root=REPO_ROOT)
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["f5_bounded_lifecycle_wiring_implemented"] is False
    assert decision["ready_for_bounded_wiring_subfamilies"] == []
    assert decision["productive_numeric_values_set_current"] == 0
    assert decision["new_authority_created"] is False
    assert decision["external_effect_authorized"] is False


def test_matrix_covers_three_subfamilies_owner_policy_only() -> None:
    rows = build_f5_subfamily_adjudication_matrix_v1()
    assert tuple(r.subfamily for r in rows) == F5_SUBFAMILY_GATE_IDS
    assert PRODUCTIVE_NUMERIC_VALUES_SET == 0
    for row in rows:
        assert row.verdict == AdjudicationVerdictV1.PARTIAL_CURRENT
        assert row.wiring_decision == F5WiringDecisionV1.OWNER_POLICY_REQUIRED
        assert row.lifecycle_required is True
        assert row.productive_value_set == 0
        assert row.evidence_refs


def test_summary_and_no_implementation_flag() -> None:
    summary = build_f5_adjudication_summary_v1(repo_root=REPO_ROOT)
    assert summary["implementation_performed"] is IMPLEMENTATION_PERFORMED is False
    assert summary["ready_for_bounded_wiring"] == []
    assert summary["productive_numeric_values_set"] == 0
