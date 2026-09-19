"""Contract tests for WP_DDO_O4_N_BARS_BAR_EVIDENCE_BRIDGE_NORMATIVE_V1."""

from __future__ import annotations

import json
from pathlib import Path

from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    IMPLEMENTED_CAPTURE_SEAMS_V0,
    SEAM_REAL_OUTCOME_HORIZON,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import OUTCOME_SCALAR_KIND_V0
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_contracts_v1 import (
    REAL_OUTCOME_HORIZON_ENGINE_WIRED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BRIDGE_DECISION = REPO_ROOT / "config/governance/ddo_o4_n_bars_bar_evidence_bridge_decision_v1.json"
SUPPLIER_DECISION = (
    REPO_ROOT / "config/governance/ddo_n_bars_bar_evidence_supplier_authority_decision_v1.json"
)
BRIDGE_SPEC = REPO_ROOT / "docs/ops/specs/DDO_O4_N_BARS_BAR_EVIDENCE_BRIDGE_NORMATIVE_V1.md"


def test_bridge_normative_spec_present() -> None:
    text = BRIDGE_SPEC.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_DDO_O4_N_BARS_BAR_EVIDENCE_BRIDGE_NORMATIVE_V1" in text
    assert text.lstrip().startswith("---")
    assert "S1_INFORMATION_SET_REF_DECISION=CLOSED" in text
    assert "S2_MEASUREMENT_EVIDENCE_DECISION=CLOSED" in text
    assert "A_BEFORE_B=true" in text


def test_bridge_decision_closes_owner_decisions_and_pipeline() -> None:
    bridge = json.loads(BRIDGE_DECISION.read_text(encoding="utf-8"))
    supplier = json.loads(SUPPLIER_DECISION.read_text(encoding="utf-8"))
    assert bridge["owner_decision_required_remaining"] == []
    assert supplier["owner_decision_required_remaining"] == []
    assert bridge["s1_information_set_ref_decision"]["status"] == "CLOSED"
    assert bridge["s2_measurement_evidence_decision"]["status"] == "CLOSED"
    assert bridge["s3_bridge_package_decision"]["placement"] == "learning_ddo_package"
    assert bridge["bridge_mints_evaluation_time_information_set_ref"] is False
    assert bridge["bridge_mints_actual_outcome_ref"] is False
    assert (
        bridge["ddo_supplier_authority_owner"]
        == supplier["authority_owner"]
        == "peak_trade.learning.ddo.n_bars_bar_evidence_supplier_v1"
    )
    assert bridge["implementation_pipeline"][-2].endswith(
        "validate_real_outcome_horizon_supplier_input_v1"
    )
    kinds = bridge["s2_measurement_evidence_decision"]["outcome_scalar_kinds"]
    assert kinds == list(OUTCOME_SCALAR_KIND_V0)


def test_runtime_guards_capture_unlock_external_effect_still_false() -> None:
    bridge = json.loads(BRIDGE_DECISION.read_text(encoding="utf-8"))
    guards = bridge["capture_and_runtime_guards"]
    assert guards["real_outcome_horizon_engine_wired"] is True
    assert guards["capture_seam_unlock"] is True
    assert guards["productive_host_join"] is True
    assert guards["evaluation_runtime_wiring"] is True
    assert guards["productive_evaluation_runtime_join"] is True
    assert REAL_OUTCOME_HORIZON_ENGINE_WIRED is True
    assert SEAM_REAL_OUTCOME_HORIZON in IMPLEMENTED_CAPTURE_SEAMS_V0
    assert guards["blocked_capture_seam_id"] is None
    assert guards["external_effect_authorized"] is False
    assert bridge["fail_closed_rule"] == "MISSING_OR_UNPROVEN_EVIDENCE_IMPLIES_NO_REAL_CLAIM"
    assert bridge["dependency_order"]["a_before_b"] is True
