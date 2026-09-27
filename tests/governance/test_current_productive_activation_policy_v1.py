"""CURRENT Productive Activation policy v1 tests."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from src.governance.current_productive_activation_policy_v1 import (
    POLICY_RECORD_CONFIG,
    RATIFIED_F1_M9_THRESHOLD_DIGEST,
    RATIFIED_F1_M9_THRESHOLD_SECONDS,
    RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
    RUNTIME_SURFACE_F1_M9_INTEGRATED_OFFLINE_REPLAY,
    STATUS_ADMISSION_GRANTED,
    canonical_policy_record_body_v1,
    evaluate_productive_runtime_admission_v1,
    load_productive_activation_policy_record_v1,
    prove_downstream_authorities_independent_v1,
    prove_p5_bind_does_not_imply_productive_activation_v1,
    standing_productive_activation_authorized_v1,
    validate_productive_activation_policy_record_v1,
)
from src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1 import (
    STATUS_WIRED,
    evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1,
)
from src.governance.governed_current_productive_activation_policy_closure_v1 import (
    prove_governed_current_productive_activation_policy_v1,
)
from src.governance.governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1 import (
    GovernedF1M9ThresholdConsumerWiringRequestV1,
    run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import (
    F1M9ProductiveApplyLedgerPathsV1,
    initialize_empty_revocation_ledger_v1,
)
from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
    F1M9ThresholdValueAuthorizationLedgerPathsV1,
    initialize_empty_threshold_revocation_ledger_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    CONTINUOUS_RUN_AUTHORIZED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    AUTONOMY_CAN_MINT_PERMIT,
    AUTONOMY_CAN_POST,
    FULL_CORE_AUTONOMY_AUTHORITY_BOUNDARY,
)
from src.ops.p5_10_productive_activation_and_binding_v1.constants_v1 import (
    P5_AUTHORITY_CUTOVER_AUTHORIZED,
    PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED,
)
from src.ops.pre_external_to_external_effect_boundary_bounded_wp_v1 import (
    prove_pre_external_to_external_effect_boundary_v1,
)
from tests.governance.test_governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1 import (
    _bound_context,
    _canonical_seam,
)
from tests.trading.master_v2.test_double_play_runtime_typed_volatility_presence_gate_v1 import (
    _valid_estimate,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_policy_valid_and_standing_authorized() -> None:
    policy = validate_productive_activation_policy_record_v1(repo_root=REPO_ROOT)
    assert policy.policy_authorized is True, policy.reason_codes
    assert standing_productive_activation_authorized_v1(repo_root=REPO_ROOT) is True
    assert prove_governed_current_productive_activation_policy_v1(repo_root=REPO_ROOT)


def test_f1_m9_lineage_unchanged() -> None:
    record = load_productive_activation_policy_record_v1(repo_root=REPO_ROOT)
    lineage = record["bound_lineage"]
    assert (
        int(lineage["ratified_threshold_numeric_max_age_seconds"])
        == RATIFIED_F1_M9_THRESHOLD_SECONDS
    )
    assert lineage["owner_threshold_record_digest"] == RATIFIED_F1_M9_THRESHOLD_DIGEST


def test_admission_granted_for_admitted_surfaces() -> None:
    for surface in (
        RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
        RUNTIME_SURFACE_F1_M9_INTEGRATED_OFFLINE_REPLAY,
    ):
        admission = evaluate_productive_runtime_admission_v1(
            runtime_surface=surface,
            repo_root=REPO_ROOT,
        )
        assert admission.admission_status == STATUS_ADMISSION_GRANTED
        assert admission.runtime_admission_granted is True
        assert admission.productive_activation_authorized is True
        assert admission.continuous_run_authorized is False
        assert admission.external_effect_authorized is False
        assert admission.post_allowed is False
        assert admission.wire_send_permitted is False
        assert admission.autonomy_can_mint_permit is False
        assert admission.autonomy_can_post is False
        assert admission.credential_access_performed is False


def test_fail_closed_wrong_surface() -> None:
    admission = evaluate_productive_runtime_admission_v1(
        runtime_surface="UNKNOWN_SURFACE",
        repo_root=REPO_ROOT,
    )
    assert admission.runtime_admission_granted is False
    assert "RUNTIME_SURFACE_NOT_ADMITTED" in admission.reason_codes


def test_fail_closed_malformed_policy_record(tmp_path: Path) -> None:
    bad = load_productive_activation_policy_record_v1(repo_root=REPO_ROOT)
    bad["policy_authorized"] = False
    path = tmp_path / "record.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    # Point loader via monkeypatch path: copy broken record to temp repo layout
    dest = tmp_path / POLICY_RECORD_CONFIG
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(bad), encoding="utf-8")
    policy = validate_productive_activation_policy_record_v1(repo_root=tmp_path)
    assert policy.policy_authorized is False


def test_fail_closed_digest_mismatch(tmp_path: Path) -> None:
    record = copy.deepcopy(load_productive_activation_policy_record_v1(repo_root=REPO_ROOT))
    record["policy_record_digest"] = "0" * 64
    dest = tmp_path / POLICY_RECORD_CONFIG
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(record), encoding="utf-8")
    policy = validate_productive_activation_policy_record_v1(repo_root=tmp_path)
    assert policy.policy_authorized is False
    assert "POLICY_RECORD_DIGEST_MISMATCH" in policy.reason_codes


def test_consumer_reachability_alone_without_policy_fails(tmp_path: Path) -> None:
    admission = evaluate_productive_runtime_admission_v1(
        runtime_surface=RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
        repo_root=tmp_path,
    )
    assert admission.runtime_admission_granted is False


def test_p5_bind_alone_does_not_imply_activation() -> None:
    assert PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED is True
    assert P5_AUTHORITY_CUTOVER_AUTHORIZED is False
    assert prove_p5_bind_does_not_imply_productive_activation_v1() is True


def test_downstream_authorities_remain_independent() -> None:
    assert prove_downstream_authorities_independent_v1() is True
    assert CONTINUOUS_RUN_AUTHORIZED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert AUTONOMY_CAN_MINT_PERMIT is False
    assert AUTONOMY_CAN_POST is False
    assert FULL_CORE_AUTONOMY_AUTHORITY_BOUNDARY == (
        "ONE_CYCLE_ORCHESTRATION_TO_PRE_EXTERNAL_EFFECT_ONLY"
    )


def test_e2e_activation_to_f1_m9_consumer_pre_external_guards(tmp_path: Path) -> None:
    apply_rev = tmp_path / "apply_rev.jsonl"
    threshold_rev = tmp_path / "threshold_rev.jsonl"
    initialize_empty_revocation_ledger_v1(apply_rev)
    initialize_empty_threshold_revocation_ledger_v1(threshold_rev)
    continuation = run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1(
        GovernedF1M9ThresholdConsumerWiringRequestV1(
            apply_ledger_paths=F1M9ProductiveApplyLedgerPathsV1(
                apply_ledger_path=tmp_path / "apply.jsonl",
                revocation_ledger_path=apply_rev,
            ),
            threshold_ledger_paths=F1M9ThresholdValueAuthorizationLedgerPathsV1(
                threshold_ledger_path=tmp_path / "threshold.jsonl",
                threshold_revocation_ledger_path=threshold_rev,
            ),
            repo_root=REPO_ROOT,
        )
    )
    assert continuation.bound_seam_record is not None
    ctx, elig = _bound_context(_valid_estimate())
    path = evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1(
        market_context=ctx,
        eligibility=elig,
        governed_seam_record=continuation.bound_seam_record,
        require_governed_seam=True,
        runtime_surface=RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
        repo_root=REPO_ROOT,
    )
    assert path.wiring_status == STATUS_WIRED
    assert path.productive_runtime_admission is True
    assert path.productive_activation_authorized is True
    assert path.external_effect_authorized is False
    pre = prove_pre_external_to_external_effect_boundary_v1()
    assert pre.ok is True


def test_policy_record_digest_recomputable() -> None:
    record = load_productive_activation_policy_record_v1(repo_root=REPO_ROOT)
    body = canonical_policy_record_body_v1(record)
    assert record["policy_record_digest"] == compute_content_sha256(body)
