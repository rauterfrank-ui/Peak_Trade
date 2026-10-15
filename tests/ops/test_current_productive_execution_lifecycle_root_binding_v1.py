"""BU01 execution lifecycle root binding contract tests (offline)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_execution_lifecycle_root_binding_v1 import (
    ExecutionLifecycleRootBindingError,
    assert_atomic_state_dir_bound_to_store_root_v1,
    assert_correlation_identity_matches_envelope_v1,
    assert_reconciliation_state_root_matches_productivity_v1,
    default_guard_atomic_state_dir_for_store_root_v1,
    resolve_canonical_reconciliation_state_root_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_mandatory_new_risk_enter_post_admission_v1 import (
    MandatoryNewRiskEnterPostAdmissionError,
    persist_enter_post_lifecycle_correlation_v1,
    prove_new_risk_enter_post_store_admission_clear_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
    FullCoreAuthorizationBindingV1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import VenuePlanCandidateV1
from tests.ops.test_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    _new_risk_envelope,
)


def _same_clordid_different_digest_envelope(*, quantity: str) -> FinalOrderEnvelopeV1:
    plan = VenuePlanCandidateV1(
        instrument_id="okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap",
        side="buy",
        quantity=quantity,
        order_type="market",
        td_mode="cross",
        reduce_only=False,
        clordid="pt-fc-one-shot-join-v1",
        venue_native_payload={
            "instId": "okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap",
            "ordType": "market",
            "side": "buy",
            "sz": quantity,
            "tdMode": "cross",
        },
        quantity_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        side_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        instrument_source="DH_CAP24_BOUND_INSTRUMENT_ID",
        path_kind="FULL_CORE_CURRENT_PRODUCTIVE",
    )
    return bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref="TEST_ADMISSION_REF",
        provenance_ref="TEST_PROVENANCE_REF",
        creation_epoch="2026-09-22T00:00:00Z",
    )


def _binding() -> FullCoreAuthorizationBindingV1:
    return FullCoreAuthorizationBindingV1(
        owner_go="OWNER_GO_TEST",
        origin_main_sha="abc",
        account_scope="acct-1",
        environment="SHADOW",
        execution_mode="OFFLINE_STUB",
        canonical_decision_id="dec-1",
        instrument_id="0G-USDT-SWAP",
        native_id="0G-USDT-SWAP",
        selected_direction="ENTER_LONG",
        order_side="buy",
        final_quantity="1",
        order_type="limit",
        order_price="1.0",
        venue_plan_digest="vp",
        envelope_digest="env-digest-placeholder",
        guard_config_digest="gc",
        session_id="sess-1",
        clordid="cl-1",
    )


def test_valid_lane_root_binding(tmp_path: Path) -> None:
    store = tmp_path / "runtime/current_productive/lane_a/post_durable_store"
    store.mkdir(parents=True)
    atomic = default_guard_atomic_state_dir_for_store_root_v1(store_root=store)
    assert_atomic_state_dir_bound_to_store_root_v1(store_root=store, atomic_state_dir=atomic)


def test_valid_attempt_correlation_persist_and_reload(tmp_path: Path) -> None:
    store = tmp_path / "store"
    store.mkdir()
    envelope = _new_risk_envelope()
    binding = replace(
        _binding(),
        envelope_digest=envelope.envelope_digest,
        clordid=envelope.client_order_id,
    )
    atomic = default_guard_atomic_state_dir_for_store_root_v1(store_root=store)
    persist_enter_post_lifecycle_correlation_v1(
        store_root=store,
        envelope=envelope,
        authorization_binding=binding,
        pretrade_decision_id="pre-1",
        submit_attempt_id="attempt-1",
        atomic_state_dir=atomic,
    )
    assert_correlation_identity_matches_envelope_v1(
        correlation={
            "envelope_digest": envelope.envelope_digest,
            "clordid": envelope.client_order_id,
            "envelope_id": envelope.envelope_id,
        },
        envelope=envelope,
    )


def test_wrong_lane_rejected_atomic_outside_store(tmp_path: Path) -> None:
    store = tmp_path / "store"
    store.mkdir()
    outside = tmp_path / "other_lane" / "atomic"
    outside.mkdir(parents=True)
    with pytest.raises(ExecutionLifecycleRootBindingError, match="OUTSIDE_STORE_ROOT"):
        assert_atomic_state_dir_bound_to_store_root_v1(store_root=store, atomic_state_dir=outside)


def test_wrong_account_rejected_on_correlation_mismatch(tmp_path: Path) -> None:
    envelope = _new_risk_envelope()
    with pytest.raises(ExecutionLifecycleRootBindingError, match="CLORDID_MISMATCH"):
        assert_correlation_identity_matches_envelope_v1(
            correlation={"clordid": "wrong-clordid", "envelope_digest": envelope.envelope_digest},
            envelope=envelope,
        )


def test_wrong_instrument_rejected_via_envelope_digest(tmp_path: Path) -> None:
    envelope = _new_risk_envelope()
    with pytest.raises(ExecutionLifecycleRootBindingError, match="DIGEST_MISMATCH"):
        assert_correlation_identity_matches_envelope_v1(
            correlation={"envelope_digest": "deadbeef", "clordid": envelope.client_order_id},
            envelope=envelope,
        )


def test_missing_root_fail_closed_persist(tmp_path: Path) -> None:
    envelope = _new_risk_envelope()
    binding = _binding()
    with pytest.raises(ExecutionLifecycleRootBindingError):
        persist_enter_post_lifecycle_correlation_v1(
            store_root=tmp_path / "missing",
            envelope=envelope,
            authorization_binding=binding,
            pretrade_decision_id="p",
            submit_attempt_id="a",
            atomic_state_dir=tmp_path / "outside" / "atomic",
        )


def test_root_mismatch_fail_closed_recon(tmp_path: Path) -> None:
    prod = tmp_path / "prod"
    (prod / "runtime_state" / "recon").mkdir(parents=True)
    wrong = tmp_path / "wrong_recon"
    wrong.mkdir()
    with pytest.raises(ExecutionLifecycleRootBindingError, match="CANONICAL_MISMATCH"):
        assert_reconciliation_state_root_matches_productivity_v1(
            productivity_root=prod,
            reconciliation_state_root=wrong,
        )


def test_valid_reconciliation_root_nested_layout(tmp_path: Path) -> None:
    prod = tmp_path / "prod"
    recon = prod / "runtime_state" / "recon"
    recon.mkdir(parents=True)
    assert resolve_canonical_reconciliation_state_root_v1(productivity_root=prod) == recon.resolve()


def test_restart_root_recovery_correlation_under_store(tmp_path: Path) -> None:
    store = tmp_path / "store"
    store.mkdir()
    envelope = _new_risk_envelope()
    binding = replace(
        _binding(),
        envelope_digest=envelope.envelope_digest,
        clordid=envelope.client_order_id,
    )
    atomic = store / "full_core_enter_post_guard_atomic_v1"
    persist_enter_post_lifecycle_correlation_v1(
        store_root=store,
        envelope=envelope,
        authorization_binding=binding,
        pretrade_decision_id="pre",
        submit_attempt_id="attempt",
        atomic_state_dir=atomic,
    )
    prove_new_risk_enter_post_store_admission_clear_v1(
        store_root=store,
        envelope=envelope,
        atomic_state_dir=atomic,
    )


def test_duplicate_attempt_idempotency_envelope_mismatch(tmp_path: Path) -> None:
    store = tmp_path / "store"
    store.mkdir()
    first = _new_risk_envelope()
    second = _same_clordid_different_digest_envelope(quantity="2")
    assert first.client_order_id == second.client_order_id
    assert first.envelope_digest != second.envelope_digest
    binding = replace(
        _binding(),
        envelope_digest=first.envelope_digest,
        clordid=first.client_order_id,
    )
    atomic = default_guard_atomic_state_dir_for_store_root_v1(store_root=store)
    persist_enter_post_lifecycle_correlation_v1(
        store_root=store,
        envelope=first,
        authorization_binding=binding,
        pretrade_decision_id="pre",
        submit_attempt_id="attempt",
        atomic_state_dir=atomic,
    )
    with pytest.raises(
        MandatoryNewRiskEnterPostAdmissionError,
        match="CORRELATION_ENVELOPE_DIGEST_MISMATCH",
    ):
        prove_new_risk_enter_post_store_admission_clear_v1(
            store_root=store,
            envelope=second,
            atomic_state_dir=atomic,
        )
