"""Bounded POST-REAL-CAMPAIGN productive handoff (POST-6800 evidence)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.governance.f1_m9_canonical_productive_candidate_adjudication_v1 import (
    adjudicate_canonical_f1_m9_productive_candidate_v1,
)
from src.governance.f1_m9_post_real_campaign_productive_handoff_bounded_completion_v1 import (
    DEFAULT_RUNTIME_AUTHORIZATION_ID,
    DEFAULT_SELECTED_CANDIDATE_ID,
    DEFAULT_SELECTED_MAX_AGE_SECONDS,
    THRESHOLD_ENFORCEMENT_AUTHORIZED,
    evaluate_f1_m9_post_real_campaign_productive_handoff_v1,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import (
    F1M9ProductiveApplyLedgerPathsV1,
    initialize_empty_revocation_ledger_v1,
)
from src.governance.f1_m9_prospective_real_campaign_durable_evidence_verification_v1 import (
    verify_f1_m9_prospective_real_campaign_durable_evidence_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)
from src.trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    NUMERIC_MAX_AGE_DECIDED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DECISION = (
    REPO_ROOT / "config/governance/f1_m9_productive_apply_execution_boundary_v1_decision_v1.json"
)


def _ledger_paths(tmp_path: Path) -> F1M9ProductiveApplyLedgerPathsV1:
    rev = tmp_path / "revocation.jsonl"
    initialize_empty_revocation_ledger_v1(rev)
    return F1M9ProductiveApplyLedgerPathsV1(
        apply_ledger_path=tmp_path / "apply.jsonl",
        revocation_ledger_path=rev,
    )


def test_durable_evidence_verifies_post_6800_campaign() -> None:
    ver = verify_f1_m9_prospective_real_campaign_durable_evidence_v1(
        repo_root=REPO_ROOT,
        expected_runtime_authorization_id=DEFAULT_RUNTIME_AUTHORIZATION_ID,
        expected_selected_candidate_id=DEFAULT_SELECTED_CANDIDATE_ID,
        expected_selected_max_age_seconds=DEFAULT_SELECTED_MAX_AGE_SECONDS,
    )
    assert ver.verified is True
    assert ver.selected_candidate_id == DEFAULT_SELECTED_CANDIDATE_ID
    assert ver.selected_max_age_seconds == DEFAULT_SELECTED_MAX_AGE_SECONDS


def test_canonical_candidate_resolved_from_durable_evidence() -> None:
    adj = adjudicate_canonical_f1_m9_productive_candidate_v1(repo_root=REPO_ROOT)
    assert adj.resolved is True
    assert adj.candidate_id == DEFAULT_SELECTED_CANDIDATE_ID
    assert adj.candidate_value == float(DEFAULT_SELECTED_MAX_AGE_SECONDS)
    assert adj.explicit_productive_authorization_resolved is True


def test_bounded_handoff_complete_without_threshold_enforcement(tmp_path: Path) -> None:
    decision = json.loads(DECISION.read_text(encoding="utf-8"))
    assert decision["real_productive_apply_authorized"] is True
    assert decision["canonical_productive_candidate_resolved"] is True
    bound_digest = decision["authorized_owner_apply_record_digest"]
    assert isinstance(bound_digest, str) and len(bound_digest) == 64

    result = evaluate_f1_m9_post_real_campaign_productive_handoff_v1(
        repo_root=REPO_ROOT,
        ledger_paths=_ledger_paths(tmp_path),
        persist_explicit_authorization_artifact=True,
    )
    assert result.handoff_status == "F1_M9_POST_REAL_CAMPAIGN_PRODUCTIVE_HANDOFF_BOUNDED_COMPLETE"
    assert result.durable_evidence_verified is True
    assert result.explicit_productive_authorization_present is True
    assert result.governed_productive_configuration_bound is True
    assert result.owner_apply_record_bound is True
    assert result.owner_apply_record_digest == bound_digest
    assert result.reason_codes == ()
    assert result.real_productive_apply_authorized is True
    assert result.authorized_productive_parameter_seam_bound is True
    assert result.authorized_value == DEFAULT_SELECTED_MAX_AGE_SECONDS
    assert result.threshold_enforcement_authorized is THRESHOLD_ENFORCEMENT_AUTHORIZED is False
    assert result.trading_decision_effect_occurred is False
    assert PRODUCTIVE_NUMERIC_VALUES_SET == 0
    assert NUMERIC_MAX_AGE_DECIDED is False


def test_handoff_denied_when_candidate_value_tampered() -> None:
    ver = verify_f1_m9_prospective_real_campaign_durable_evidence_v1(
        repo_root=REPO_ROOT,
        expected_selected_max_age_seconds=999,
    )
    assert ver.verified is False
    assert "SELECTED_MAX_AGE_MISMATCH" in ver.reason_codes
