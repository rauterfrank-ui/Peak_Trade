"""Contract tests for WP_DDO_CANONICAL_N_BARS_BAR_EVIDENCE_SUPPLIER_AUTHORITY_NORMATIVE_V1."""

from __future__ import annotations

import json
from pathlib import Path

from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    IMPLEMENTED_CAPTURE_SEAMS_V0,
    SEAM_REAL_OUTCOME_HORIZON,
)
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_contracts_v1 import (
    REAL_OUTCOME_HORIZON_ENGINE_WIRED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DECISION_PATH = (
    REPO_ROOT / "config/governance/ddo_n_bars_bar_evidence_supplier_authority_decision_v1.json"
)
NORMATIVE_SPEC = (
    REPO_ROOT / "docs/ops/specs/DDO_N_BARS_BAR_EVIDENCE_SUPPLIER_AUTHORITY_NORMATIVE_V1.md"
)


def test_normative_spec_and_decision_record_present() -> None:
    assert NORMATIVE_SPEC.is_file()
    assert DECISION_PATH.is_file()
    text = NORMATIVE_SPEC.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_DDO_N_BARS_BAR_EVIDENCE_SUPPLIER_AUTHORITY_NORMATIVE_V1" in text
    assert text.lstrip().startswith("---")
    assert "OWNER_ADJUDICATION_BOUND=true" in text
    assert "A_BEFORE_B=true" in text


def test_machine_readable_decision_aligns_with_runtime_guards() -> None:
    decision = json.loads(DECISION_PATH.read_text(encoding="utf-8"))
    assert decision["owner_adjudication_bound"] is True
    assert decision["authority_owner"] == "peak_trade.learning.ddo.n_bars_bar_evidence_supplier_v1"
    assert (
        decision["s2_reuse_decision"]
        == "O4_VIA_GOVERNED_BRIDGE_REQUIRED_AND_DDO_LEARNING_SUPPLIER_REQUIRED"
    )
    assert decision["reuse_options"]["A_direct_existing_producer_reuse"] == "REJECTED"
    guards = decision["capture_and_runtime_guards"]
    assert guards["real_outcome_horizon_engine_wired"] is True
    assert guards["capture_seam_unlock"] is True
    assert guards["productive_host_join"] is True
    assert guards["evaluation_runtime_wiring"] is True
    assert guards["productive_evaluation_runtime_join"] is True
    assert REAL_OUTCOME_HORIZON_ENGINE_WIRED is True
    assert SEAM_REAL_OUTCOME_HORIZON in IMPLEMENTED_CAPTURE_SEAMS_V0
    assert guards["blocked_capture_seam_id"] is None


def test_fail_closed_and_dependency_preserved_in_decision() -> None:
    decision = json.loads(DECISION_PATH.read_text(encoding="utf-8"))
    assert decision["fail_closed_rule"] == "MISSING_OR_UNPROVEN_EVIDENCE_IMPLIES_NO_REAL_CLAIM"
    assert decision["dependency_order"]["a_before_b"] is True
    assert decision["fixture_productive_authority"] is False
    assert decision["implementation_authorized_this_slice"] is False
    assert decision["bridge_contract_status"] == "NORMATIVE_BOUND"
    assert decision["owner_decision_required_remaining"] == []
