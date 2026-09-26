"""F1/M9 Owner threshold value ratification (600s) real mechanical continuation tests."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.f1_m9_owner_threshold_value_ratification_artifacts_v1 import (
    load_owner_threshold_record_artifact_v1,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import (
    F1M9ProductiveApplyLedgerPathsV1,
    initialize_empty_revocation_ledger_v1,
)
from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
    F1M9ThresholdValueAuthorizationLedgerPathsV1,
    initialize_empty_threshold_revocation_ledger_v1,
)
from src.governance.governed_f1_m9_scoped_owner_threshold_value_ratification_closure_v1 import (
    prove_governed_f1_m9_scoped_owner_threshold_value_ratification_v1,
)
from src.governance.governed_f1_m9_scoped_owner_threshold_value_ratification_evidence_v1 import (
    F1M9ThresholdRatificationPhaseStateV1,
)
from src.governance.governed_f1_m9_scoped_owner_threshold_value_ratification_real_mechanical_continuation_v1 import (
    DECISION_CONFIG,
    GovernedF1M9ThresholdValueRatificationRequestV1,
    PRODUCTIVE_ACTIVATION_AUTHORIZED,
    RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS,
    REAL_P4_TO_F1_M9_JOIN_STATUS,
    run_governed_f1_m9_scoped_owner_threshold_value_ratification_continuation_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    EXTERNAL_EFFECT,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)
from src.trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    ENFORCEMENT_ENABLED,
    NUMERIC_MAX_AGE_DECIDED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _apply_ledger_paths(tmp_path: Path) -> F1M9ProductiveApplyLedgerPathsV1:
    rev = tmp_path / "apply_revocation.jsonl"
    initialize_empty_revocation_ledger_v1(rev)
    return F1M9ProductiveApplyLedgerPathsV1(
        apply_ledger_path=tmp_path / "apply.jsonl",
        revocation_ledger_path=rev,
    )


def _threshold_ledger_paths(tmp_path: Path) -> F1M9ThresholdValueAuthorizationLedgerPathsV1:
    rev = tmp_path / "threshold_revocation.jsonl"
    initialize_empty_threshold_revocation_ledger_v1(rev)
    return F1M9ThresholdValueAuthorizationLedgerPathsV1(
        threshold_ledger_path=tmp_path / "threshold.jsonl",
        threshold_revocation_ledger_path=rev,
    )


def test_threshold_value_ratification_continuation_complete(tmp_path: Path) -> None:
    result = run_governed_f1_m9_scoped_owner_threshold_value_ratification_continuation_v1(
        GovernedF1M9ThresholdValueRatificationRequestV1(
            apply_ledger_paths=_apply_ledger_paths(tmp_path),
            threshold_ledger_paths=_threshold_ledger_paths(tmp_path),
            repo_root=REPO_ROOT,
            persist_durable_threshold_record=True,
        )
    )
    assert result.status == "CONTINUATION_COMPLETE", result.blocking_reasons
    assert result.threshold_hot_path_ratified is True
    assert result.exact_value_authority_valid is True
    assert result.f1_m9_value_binding_valid is True
    assert result.real_p4_to_f1_m9_join_status == REAL_P4_TO_F1_M9_JOIN_STATUS
    assert result.productive_activation_authorized is False
    assert result.owner_threshold_record_digest is not None
    assert result.ratification_evidence is not None
    assert (
        result.ratification_evidence.phase_state
        == F1M9ThresholdRatificationPhaseStateV1.RATIFICATION_COMPLETED
    )
    assert result.ratification_evidence.threshold_numeric_max_age_seconds == float(
        RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS
    )
    artifact = load_owner_threshold_record_artifact_v1(repo_root=REPO_ROOT)
    assert artifact is not None
    assert float(artifact["threshold_numeric_max_age_seconds"]) == 600.0


def test_global_invariants_preserved() -> None:
    assert PRODUCTIVE_ACTIVATION_AUTHORIZED is False
    assert EXTERNAL_EFFECT is False
    assert PRODUCTIVE_NUMERIC_VALUES_SET == 0
    assert NUMERIC_MAX_AGE_DECIDED is False
    assert ENFORCEMENT_ENABLED is False


def test_closure_proof() -> None:
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    artifact = load_owner_threshold_record_artifact_v1(repo_root=REPO_ROOT)
    assert artifact is not None
    digest = str(artifact["threshold_value_authorization_record_digest"])
    assert decision.get("owner_threshold_record_digest_bound") == digest
    assert prove_governed_f1_m9_scoped_owner_threshold_value_ratification_v1(repo_root=REPO_ROOT)
