"""CURRENT Continuous Run policy v1 tests."""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

from src.governance.current_continuous_run_policy_v1 import (
    POLICY_RECORD_CONFIG,
    RATIFIED_F1_M9_THRESHOLD_DIGEST,
    RATIFIED_F1_M9_THRESHOLD_SECONDS,
    STATUS_ADMISSION_GRANTED,
    TARGET_ORCHESTRATOR_SURFACE,
    canonical_policy_record_body_v1,
    evaluate_continuous_runtime_admission_v1,
    load_continuous_run_policy_record_v1,
    prove_continuous_run_does_not_imply_external_effect_v1,
    prove_productive_activation_does_not_imply_continuous_run_v1,
    standing_continuous_run_authorized_v1,
    validate_continuous_run_policy_record_v1,
)
from src.governance.current_continuous_run_runtime_binding_v1 import (
    ContinuousRunRuntimeBindingError,
    run_policy_governed_current_productive_continuous_cycle_run_v1,
)
from src.governance.current_productive_activation_policy_v1 import (
    RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
    evaluate_productive_runtime_admission_v1,
    standing_productive_activation_authorized_v1,
)
from src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1 import (
    STATUS_WIRED,
    evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1,
)
from src.governance.governed_current_continuous_run_policy_closure_v1 import (
    prove_governed_current_continuous_run_policy_v1,
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
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    CONTINUOUS_RUN_AUTHORIZED,
    DISPOSITION_FAIL_CLOSED,
    DISPOSITION_MAX_CYCLES,
    RUNTIME_OWNER_GO,
    CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
    InjectedContinuousObservationV1,
    ScriptedContinuousObservationSourceV1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    AUTONOMY_CAN_MINT_PERMIT,
    AUTONOMY_CAN_POST,
    run_current_productive_governed_cycle_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from tests.governance.test_governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1 import (
    _bound_context,
    _canonical_seam,
)
from tests.ops.test_full_core_current_productive_governed_continuous_cycle_orchestrator_v1 import (
    C1_A,
    C1_B,
    CURSOR_FLOOR,
    NATIVE_ID,
    ORIGIN_SHA,
    _FakeClock,
    _obs,
    _seed_cursor,
)
from tests.trading.master_v2.test_double_play_runtime_typed_volatility_presence_gate_v1 import (
    _valid_estimate,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _seed_policy_tree(tmp_path: Path) -> Path:
    for rel in (
        POLICY_RECORD_CONFIG,
        "config/governance/current_continuous_run_policy_owner_go_v1_decision.json",
        "config/governance/current_productive_activation_policy_v1_record.json",
        "config/governance/current_productive_activation_policy_owner_go_v1_decision.json",
        "config/governance/productive_activation_boundary_forensic_review_v1_decision_v1.json",
        "config/governance/governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1_decision_v1.json",
        "config/governance/governed_f1_m9_scoped_owner_productive_runtime_apply_start_real_mechanical_continuation_v1_decision_v1.json",
    ):
        src = REPO_ROOT / rel
        dest = tmp_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dest)
    return tmp_path


def _auth() -> CurrentProductiveGovernedContinuousCycleRunAuthorizationV1:
    return CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(
        continuous_owner_go=RUNTIME_OWNER_GO,
        native_id=NATIVE_ID,
        bar="1m",
        expected_cursor_floor=CURSOR_FLOOR,
        max_cycles_per_run=2,
        max_run_duration_seconds=90.0,
        wait_interval_seconds=1.0,
        max_wait_for_next_c1_seconds=30.0,
        stall_seconds=30.0,
    )


def _f1_m9_evaluator_factory(tmp_path: Path):
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

    def _eval(_cycle_index: int):
        return evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1(
            market_context=ctx,
            eligibility=elig,
            governed_seam_record=continuation.bound_seam_record,
            require_governed_seam=True,
            runtime_surface=RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
            repo_root=REPO_ROOT,
        )

    return _eval


def test_policy_valid_and_standing_authorized() -> None:
    policy = validate_continuous_run_policy_record_v1(repo_root=REPO_ROOT)
    assert policy.policy_authorized is True, policy.reason_codes
    assert standing_continuous_run_authorized_v1(repo_root=REPO_ROOT) is True
    assert prove_governed_current_continuous_run_policy_v1(repo_root=REPO_ROOT)


def test_f1_m9_lineage_unchanged() -> None:
    record = load_continuous_run_policy_record_v1(repo_root=REPO_ROOT)
    lineage = record["bound_lineage"]
    assert (
        int(lineage["ratified_threshold_numeric_max_age_seconds"])
        == RATIFIED_F1_M9_THRESHOLD_SECONDS
    )
    assert lineage["owner_threshold_record_digest"] == RATIFIED_F1_M9_THRESHOLD_DIGEST


def test_fail_closed_missing_policy(tmp_path: Path) -> None:
    policy = validate_continuous_run_policy_record_v1(repo_root=tmp_path)
    assert policy.policy_authorized is False
    assert "POLICY_RECORD_MISSING" in policy.reason_codes


def test_fail_closed_unauthorized_policy(tmp_path: Path) -> None:
    _seed_policy_tree(tmp_path)
    record = load_continuous_run_policy_record_v1(repo_root=tmp_path)
    record["policy_authorized"] = False
    path = tmp_path / POLICY_RECORD_CONFIG
    path.write_text(json.dumps(record), encoding="utf-8")
    policy = validate_continuous_run_policy_record_v1(repo_root=tmp_path)
    assert policy.policy_authorized is False
    assert "POLICY_NOT_AUTHORIZED" in policy.reason_codes


def test_fail_closed_digest_mismatch(tmp_path: Path) -> None:
    _seed_policy_tree(tmp_path)
    record = copy.deepcopy(load_continuous_run_policy_record_v1(repo_root=tmp_path))
    record["policy_record_digest"] = "0" * 64
    (tmp_path / POLICY_RECORD_CONFIG).write_text(json.dumps(record), encoding="utf-8")
    policy = validate_continuous_run_policy_record_v1(repo_root=tmp_path)
    assert "POLICY_RECORD_DIGEST_MISMATCH" in policy.reason_codes


def test_fail_closed_wrong_orchestrator_target() -> None:
    admission = evaluate_continuous_runtime_admission_v1(
        runtime_surface=RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
        repo_root=REPO_ROOT,
        orchestrator_target="WRONG_TARGET",
    )
    assert admission.continuous_runtime_admission_granted is False
    assert "ORCHESTRATOR_TARGET_MISMATCH" in admission.reason_codes


def test_productive_activation_alone_cannot_start_continuous_run(tmp_path: Path) -> None:
    assert standing_productive_activation_authorized_v1(repo_root=REPO_ROOT) is True
    admission = evaluate_productive_runtime_admission_v1(
        runtime_surface=RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
        repo_root=REPO_ROOT,
    )
    assert admission.continuous_run_authorized is False
    assert validate_continuous_run_policy_record_v1(repo_root=tmp_path).policy_authorized is False


def test_productive_activation_absent_blocks_continuous_run(tmp_path: Path) -> None:
    _seed_policy_tree(tmp_path)
    bad = tmp_path / "config/governance/current_productive_activation_policy_v1_record.json"
    payload = json.loads(bad.read_text(encoding="utf-8"))
    payload["policy_authorized"] = False
    bad.write_text(json.dumps(payload), encoding="utf-8")
    policy = validate_continuous_run_policy_record_v1(repo_root=tmp_path)
    assert policy.policy_authorized is False
    assert "PRODUCTIVE_ACTIVATION_PREREQUISITE_INVALID" in policy.reason_codes


def test_admission_granted_with_valid_policy() -> None:
    admission = evaluate_continuous_runtime_admission_v1(
        runtime_surface=RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
        repo_root=REPO_ROOT,
        orchestrator_target=TARGET_ORCHESTRATOR_SURFACE,
    )
    assert admission.admission_status == STATUS_ADMISSION_GRANTED
    assert admission.continuous_runtime_admission_granted is True
    assert admission.continuous_run_authorized is True
    assert admission.productive_activation_authorized is True
    assert admission.external_effect_authorized is False
    assert admission.post_allowed is False
    assert admission.autonomy_can_mint_permit is False
    assert admission.autonomy_can_post is False


def test_semantic_collision_guards() -> None:
    assert prove_productive_activation_does_not_imply_continuous_run_v1(repo_root=REPO_ROOT)
    assert prove_continuous_run_does_not_imply_external_effect_v1()
    assert CONTINUOUS_RUN_AUTHORIZED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert AUTONOMY_CAN_MINT_PERMIT is False
    assert AUTONOMY_CAN_POST is False


def test_policy_record_digest_recomputable() -> None:
    record = load_continuous_run_policy_record_v1(repo_root=REPO_ROOT)
    body = canonical_policy_record_body_v1(record)
    assert record["policy_record_digest"] == compute_content_sha256(body)


def test_multi_cycle_policy_governed_run_with_f1_m9(tmp_path: Path) -> None:
    from tests.ops.test_full_core_current_productive_governed_continuous_cycle_orchestrator_v1 import (
        _eg_stub,
        _t2_hold,
    )

    cursor_store = _seed_cursor(tmp_path, event_time=CURSOR_FLOOR)
    clock = _FakeClock()
    f1_eval = _f1_m9_evaluator_factory(tmp_path)
    result = run_policy_governed_current_productive_continuous_cycle_run_v1(
        authorization=_auth(),
        origin_main_sha=ORIGIN_SHA,
        cursor_store_root=cursor_store,
        lock_root=tmp_path / "lock",
        evidence_root=tmp_path / "evidence",
        observation_source=ScriptedContinuousObservationSourceV1([_obs(C1_A), None, _obs(C1_B)]),
        repo_root=REPO_ROOT,
        f1_m9_cycle_evaluator=f1_eval,
        eg_cycle_dispatch=_eg_stub,
        t2_cycle_dispatch=_t2_hold,
        s5_runner=run_current_productive_governed_cycle_v1,
        time_fn=clock.time,
        sleep_fn=clock.sleep,
    )
    orch = result.orchestrator_result
    assert orch.disposition == DISPOSITION_MAX_CYCLES
    assert orch.cycles_completed == 2
    assert orch.post_count == 0
    assert orch.permit_created is False
    assert result.external_effect_authorized is False
    assert result.autonomy_can_mint_permit is False
    assert result.autonomy_can_post is False
    cycle_gates = [e for e in result.iteration_evidence if e.cycle_index >= 1]
    assert len(cycle_gates) >= 2
    for gate in cycle_gates:
        assert gate.continuous_admission_granted is True
        assert gate.productive_activation_authorized is True
        assert gate.f1_m9_wiring_status == STATUS_WIRED
        assert gate.f1_m9_threshold_seconds == 600.0


def test_revocation_between_cycles_prevents_cycle_two(tmp_path: Path) -> None:
    from tests.ops.test_full_core_current_productive_governed_continuous_cycle_orchestrator_v1 import (
        _eg_stub,
        _t2_hold,
    )

    cursor_store = _seed_cursor(tmp_path, event_time=CURSOR_FLOOR)
    clock = _FakeClock()
    f1_eval = _f1_m9_evaluator_factory(tmp_path)
    calls = {"n": 0}
    real_eval = evaluate_continuous_runtime_admission_v1

    def flaky_admission(**kwargs):
        calls["n"] += 1
        if calls["n"] <= 2:
            return real_eval(**kwargs)
        return real_eval(**kwargs).__class__(
            admission_status="CONTINUOUS_RUNTIME_ADMISSION_DENIED_FAIL_CLOSED",
            continuous_runtime_admission_granted=False,
            continuous_run_authorized=False,
            productive_activation_authorized=False,
            productive_runtime_admission=False,
            runtime_surface=kwargs.get("runtime_surface"),
            policy_record_digest=None,
            productive_activation_policy_digest=None,
            reason_codes=("REVOKED_FOR_TEST",),
            external_effect_authorized=False,
            post_allowed=False,
            wire_send_permitted=False,
            real_venue_post_allowed=False,
            autonomy_can_mint_permit=False,
            autonomy_can_post=False,
            credential_access_performed=False,
        )

    with mock.patch(
        "src.governance.current_continuous_run_runtime_binding_v1.evaluate_continuous_runtime_admission_v1",
        side_effect=flaky_admission,
    ):
        result = run_policy_governed_current_productive_continuous_cycle_run_v1(
            authorization=_auth(),
            origin_main_sha=ORIGIN_SHA,
            cursor_store_root=cursor_store,
            lock_root=tmp_path / "lock2",
            evidence_root=tmp_path / "evidence2",
            observation_source=ScriptedContinuousObservationSourceV1(
                [_obs(C1_A), None, _obs(C1_B)]
            ),
            repo_root=REPO_ROOT,
            f1_m9_cycle_evaluator=f1_eval,
            eg_cycle_dispatch=_eg_stub,
            t2_cycle_dispatch=_t2_hold,
            s5_runner=run_current_productive_governed_cycle_v1,
            time_fn=clock.time,
            sleep_fn=clock.sleep,
        )
    assert result.orchestrator_result.disposition == DISPOSITION_FAIL_CLOSED
    assert result.orchestrator_result.cycles_completed == 1
    assert "REVOKED_FOR_TEST" in result.orchestrator_result.reason_code or (
        result.orchestrator_result.reason_code == "ITERATION_AUTHORITY_GATE_DENIED"
    )


def test_binding_denied_without_policy(tmp_path: Path) -> None:
    with pytest.raises(ContinuousRunRuntimeBindingError, match="CONTINUOUS_RUN_POLICY_DENIED"):
        run_policy_governed_current_productive_continuous_cycle_run_v1(
            authorization=_auth(),
            origin_main_sha=ORIGIN_SHA,
            cursor_store_root=tmp_path,
            lock_root=tmp_path / "lock",
            evidence_root=tmp_path / "evidence",
            observation_source=ScriptedContinuousObservationSourceV1([_obs(C1_A)]),
            repo_root=tmp_path,
            f1_m9_cycle_evaluator=lambda _i: SimpleNamespace(
                wiring_status=STATUS_WIRED,
                reason_codes=(),
                threshold_numeric_max_age_seconds=600.0,
                external_effect_authorized=False,
            ),
        )


def test_productive_activation_regression_still_green() -> None:
    from tests.governance.test_current_productive_activation_policy_v1 import (
        test_policy_valid_and_standing_authorized,
    )

    test_policy_valid_and_standing_authorized()
