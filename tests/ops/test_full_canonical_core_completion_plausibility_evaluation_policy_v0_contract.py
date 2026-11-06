"""Contract tests for full canonical core completion plausibility evaluation policy v0."""

from __future__ import annotations

import json
from pathlib import Path

from src.research.full_canonical_core_completion_plausibility_evaluation_v0 import (
    EVIDENCE_CLASS_ID,
    OWNER_POLICY_REL,
    PURPOSE,
    compute_owner_policy_decision_digest_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = REPO_ROOT / OWNER_POLICY_REL


class TestFullCanonicalCoreCompletionPlausibilityEvaluationPolicyV0Contract:
    def test_policy_config_is_valid_json_with_required_fields(self) -> None:
        payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        assert payload["owner"] == "Frank Rauter"
        assert payload["evidence_class"] == EVIDENCE_CLASS_ID
        assert payload["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert payload["purpose"] == PURPOSE
        assert payload["promotion_admissible"] is False
        assert payload["runtime_admissible"] is False
        assert payload["economic_validity_claim_allowed"] is False
        assert payload["live_authorized"] is False
        assert payload["orders_allowed"] is False
        assert payload["scheduler_runtime_allowed"] is False
        assert payload["shadow_authorized"] is False
        assert payload["paper_authorized"] is False
        assert payload["testnet_authorized"] is False
        assert payload["canary_authorized"] is False
        assert payload["adapter_submission_allowed"] is False
        assert payload["credential_access_allowed"] is False
        assert payload["historical_negative_evidence_reclassification_allowed"] is False
        assert payload["unmodified_binding_retry_global_override"] is False
        assert payload["system_diagnostic_only"] is True
        assert payload["tolerated_untracked_artefacts"] == [
            ".python-version",
            ".comparison_ssot_pytest_outputs/",
        ]

    def test_policy_digest_is_manifest_bound(self) -> None:
        payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        expected = compute_owner_policy_decision_digest_v0(payload)
        assert payload["owner_policy_decision_digest"] == expected

    def test_policy_path_is_canonical(self) -> None:
        assert POLICY_PATH == REPO_ROOT / (
            "config/research/full_canonical_core_completion_plausibility_evaluation_policy_v0.json"
        )
