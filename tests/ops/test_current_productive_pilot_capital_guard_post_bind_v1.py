"""Offline adversarial proofs for pilot capital guard Enter-POST bind + DW wiring."""

from __future__ import annotations

import json
import socket
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_full_core_capital_guard_v1 import (
    ratified_offline_full_core_guard_config_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_pilot_capital_guard_post_bind_v1 import (
    OWNER_GO_CURRENT_PILOT_CAPITAL_GUARD_POST_BIND_V1,
    PilotCapitalGuardPostBindError,
    enforce_pilot_capital_guard_before_enter_post_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_exact_object_flatten_plan_v1 import (
    INSTRUMENT_SOURCE as EXACT_OBJECT_FLATTEN_INSTRUMENT_SOURCE,
    PATH_KIND_EXACT_OBJECT_FLATTEN,
    QUANTITY_SOURCE as EXACT_OBJECT_FLATTEN_QUANTITY_SOURCE,
    SIDE_SOURCE as EXACT_OBJECT_FLATTEN_SIDE_SOURCE,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_mandatory_new_risk_enter_post_admission_v1 import (
    ProductiveVenuePostRiskClassV1,
    classify_productive_venue_post_risk_class_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_risk_reducing_envelope_provenance_v1 import (
    EXACT_OBJECT_FLATTEN_ADMISSION_REF,
    EXACT_OBJECT_FLATTEN_PROVENANCE_REF,
    RiskReducingEnvelopeProvenanceError,
)
from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
    FullCoreEnvelopeBoundSendSeamError,
    assert_post_payload_reduce_only_matches_envelope_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FullCoreFinalOrderEnvelopeError,
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_join_v1 import (
    FullCoreCapitalGuardJoinMode,
    resolve_full_core_capital_guard_join_mode_v1,
    run_full_core_pre_post_capital_guard_join_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import VenuePlanCandidateV1
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
    EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
    OWNER_GO,
    CurrentProductiveActualVenuePostError,
    execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1,
)
from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
    MockCurrentProductive29PIntegrityBackendV1,
)
from tests.ops._pilot_guard_enter_post_test_helpers_v1 import (
    PILOT_TEST_ACCOUNT_UID as ACCOUNT_UID,
    PILOT_TEST_INST as INST,
    PilotGuardReadTransport,
    mandatory_new_risk_execute_kwargs,
    ratified_pilot_guard_config_for_tests,
)
from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
    _FakeKeychainBackend,
    _TimeoutOpener,
)


@pytest.fixture(autouse=True)
def _forbid_real_sockets(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("NETWORK_FORBIDDEN")

    monkeypatch.setattr(socket, "create_connection", _boom)
    monkeypatch.setattr(socket.socket, "connect", _boom)


def _manual_reduce_only_envelope(*, provenance_ref: str = "TEST_PROVENANCE_REF") -> Any:
    plan = VenuePlanCandidateV1(
        instrument_id="okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap",
        side="sell",
        quantity="1",
        order_type="market",
        td_mode="cross",
        reduce_only=True,
        clordid="pt-manual-reduce-only-v1",
        venue_native_payload={
            "instId": INST,
            "ordType": "market",
            "side": "sell",
            "sz": "1",
            "tdMode": "cross",
            "reduceOnly": True,
        },
        quantity_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        side_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        instrument_source="DH_CAP24_BOUND_INSTRUMENT_ID",
        path_kind="FULL_CORE_CURRENT_PRODUCTIVE",
    )
    return bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref="TEST_ADMISSION_REF",
        provenance_ref=provenance_ref,
        creation_epoch="2026-10-14T00:00:00Z",
    )


def _authorized_exact_object_flatten_envelope(*, clordid: str = "pt-exact-flatten-v1") -> Any:
    plan = VenuePlanCandidateV1(
        instrument_id="okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap",
        side="sell",
        quantity="1",
        order_type="limit",
        td_mode="cross",
        reduce_only=True,
        clordid=clordid,
        venue_native_payload={
            "instId": INST,
            "ordType": "limit",
            "side": "sell",
            "sz": "1",
            "tdMode": "cross",
            "reduceOnly": True,
            "px": "10.0",
        },
        quantity_source=EXACT_OBJECT_FLATTEN_QUANTITY_SOURCE,
        side_source=EXACT_OBJECT_FLATTEN_SIDE_SOURCE,
        instrument_source=EXACT_OBJECT_FLATTEN_INSTRUMENT_SOURCE,
        path_kind=PATH_KIND_EXACT_OBJECT_FLATTEN,
    )
    return bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref=EXACT_OBJECT_FLATTEN_ADMISSION_REF,
        provenance_ref=EXACT_OBJECT_FLATTEN_PROVENANCE_REF,
        creation_epoch="2026-10-14T00:00:00Z",
    )


def _envelope() -> Any:
    plan = VenuePlanCandidateV1(
        instrument_id="okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap",
        side="buy",
        quantity="1",
        order_type="market",
        td_mode="cross",
        reduce_only=False,
        clordid="pt-pilot-capital-guard-v1",
        venue_native_payload={
            "instId": INST,
            "ordType": "market",
            "side": "buy",
            "sz": "1",
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
        creation_epoch="2026-10-14T00:00:00Z",
    )


def _ratified_cfg():
    return ratified_pilot_guard_config_for_tests()


def test_pilot_enforce_mode_not_reachable_from_env_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "PEAK_TRADE_FULL_CORE_CAPITAL_GUARD_JOIN_MODE",
        FullCoreCapitalGuardJoinMode.PRODUCTIVE_PILOT_ENFORCE.value,
    )
    assert (
        resolve_full_core_capital_guard_join_mode_v1()
        is FullCoreCapitalGuardJoinMode.DISABLED
    )


def test_pilot_go_denied_without_token() -> None:
    envelope = _envelope()
    with pytest.raises(PilotCapitalGuardPostBindError, match="PILOT_CAPITAL_GUARD_BIND_GO_DENIED"):
        enforce_pilot_capital_guard_before_enter_post_v1(
            pilot_capital_guard_bind_go="NOT_A_GO",
            envelope=envelope,
            read_only_get_transport=PilotGuardReadTransport(),
            pretrade_decision_id="pre-1",
            native_instrument_id=INST,
            canonical_decision_id="dec-1",
            account_identity=None,
            origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            guard_config=_ratified_cfg(),
            atomic_state_dir=Path("/tmp/unused"),
        )


def test_unratified_caps_block_enforce(tmp_path: Path) -> None:
    envelope = _envelope()
    cfg = replace(_ratified_cfg(), owner_caps_ratified=False)
    result = enforce_pilot_capital_guard_before_enter_post_v1(
        pilot_capital_guard_bind_go=OWNER_GO_CURRENT_PILOT_CAPITAL_GUARD_POST_BIND_V1,
        envelope=envelope,
        read_only_get_transport=PilotGuardReadTransport(),
        pretrade_decision_id="pre-2",
        native_instrument_id=INST,
        canonical_decision_id="dec-2",
        account_identity=None,
        origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        guard_config=cfg,
        atomic_state_dir=tmp_path / "atomic",
    )
    assert result.blocked is True
    assert any("OWNER_CAPS_UNRATIFIED" in r for r in result.reasons)


def test_pending_order_blocks(tmp_path: Path) -> None:
    envelope = _envelope()
    with pytest.raises(PilotCapitalGuardPostBindError, match="OPEN_ORDER_PRESENT"):
        enforce_pilot_capital_guard_before_enter_post_v1(
            pilot_capital_guard_bind_go=OWNER_GO_CURRENT_PILOT_CAPITAL_GUARD_POST_BIND_V1,
            envelope=envelope,
            read_only_get_transport=PilotGuardReadTransport(open_orders=True),
            pretrade_decision_id="pre-3",
            native_instrument_id=INST,
            canonical_decision_id="dec-3",
            account_identity=None,
            origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            guard_config=_ratified_cfg(),
            atomic_state_dir=tmp_path / "atomic",
        )


def test_pilot_enforce_reserves_and_passes_with_ratified_caps(tmp_path: Path) -> None:
    envelope = _envelope()
    result = enforce_pilot_capital_guard_before_enter_post_v1(
        pilot_capital_guard_bind_go=OWNER_GO_CURRENT_PILOT_CAPITAL_GUARD_POST_BIND_V1,
        envelope=envelope,
        read_only_get_transport=PilotGuardReadTransport(avail_eq="10000"),
        pretrade_decision_id="pre-4",
        native_instrument_id=INST,
        canonical_decision_id="dec-4",
        account_identity=None,
        origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        guard_config=_ratified_cfg(),
        atomic_state_dir=tmp_path / "atomic",
    )
    assert result.blocked is False
    assert result.join_result.reservation_created is True
    assert result.join_result.join_mode == FullCoreCapitalGuardJoinMode.PRODUCTIVE_PILOT_ENFORCE.value
    assert result.dw_wiring_config.apply_durable_atomic_state is False
    assert result.authorization_binding.clordid == envelope.client_order_id


def test_new_risk_post_without_pilot_go_blocked(tmp_path: Path) -> None:
    envelope = _envelope()
    with pytest.raises(
        CurrentProductiveActualVenuePostError,
        match="NEW_RISK_POST_MANDATORY_PILOT_CAPITAL_GUARD_BIND_GO_REQUIRED",
    ):
        execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
            owner_go=OWNER_GO,
            baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            envelope=envelope,
            store_root=tmp_path,
            evidence_root=tmp_path / "evidence",
            perform_real_venue_post=True,
            k1_backend=_FakeKeychainBackend(),
            opener_factory=lambda: _TimeoutOpener(),
            read_only_get_transport=PilotGuardReadTransport(),
            execution_integrity_backend=MockCurrentProductive29PIntegrityBackendV1(
                origin_main=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                head=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                drift="",
            ),
        )
    assert not (
        tmp_path / "full_core_current_productive_actual_venue_post_owner_go_consume_v1.json"
    ).is_file()


def test_new_risk_post_with_mandatory_binding_reaches_mock_post(tmp_path: Path) -> None:
    envelope = _envelope()
    result = execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
        owner_go=OWNER_GO,
        baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        envelope=envelope,
        store_root=tmp_path,
        evidence_root=tmp_path / "evidence",
        perform_real_venue_post=True,
        k1_backend=_FakeKeychainBackend(),
        opener_factory=lambda: _TimeoutOpener(),
        read_only_get_transport=PilotGuardReadTransport(avail_eq="10000"),
        execution_integrity_backend=MockCurrentProductive29PIntegrityBackendV1(
            origin_main=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            head=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            drift="",
        ),
        **mandatory_new_risk_execute_kwargs(tmp_path),
    )
    assert result.post_outcome == "UNKNOWN_EXTERNAL_EFFECT_POSSIBLE"
    assert (
        tmp_path / "full_core_mandatory_new_risk_enter_post_lifecycle_correlation_v1.json"
    ).is_file()


def test_unratified_caps_block_new_risk_post_before_owner_go_consume(tmp_path: Path) -> None:
    envelope = _envelope()
    cfg = replace(_ratified_cfg(), owner_caps_ratified=False)
    with pytest.raises(
        CurrentProductiveActualVenuePostError,
        match="NEW_RISK_POST_OWNER_CAPS_UNRATIFIED",
    ):
        execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
            owner_go=OWNER_GO,
            baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            envelope=envelope,
            store_root=tmp_path,
            evidence_root=tmp_path / "evidence",
            perform_real_venue_post=True,
            k1_backend=_FakeKeychainBackend(),
            opener_factory=lambda: _TimeoutOpener(),
            read_only_get_transport=PilotGuardReadTransport(),
            execution_integrity_backend=MockCurrentProductive29PIntegrityBackendV1(
                origin_main=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                head=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                drift="",
            ),
            pilot_capital_guard_bind_go=OWNER_GO_CURRENT_PILOT_CAPITAL_GUARD_POST_BIND_V1,
            pilot_capital_guard_config=cfg,
            pilot_native_instrument_id=INST,
            pilot_atomic_state_dir=tmp_path / "atomic",
        )


def test_reduce_only_post_exempt_from_mandatory_entry_guard(tmp_path: Path) -> None:
    envelope = _authorized_exact_object_flatten_envelope(clordid="pt-pilot-reduce-only-v1")
    assert (
        classify_productive_venue_post_risk_class_v1(envelope)
        is ProductiveVenuePostRiskClassV1.RISK_REDUCING
    )
    result = execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
        owner_go=OWNER_GO,
        baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        envelope=envelope,
        store_root=tmp_path,
        evidence_root=tmp_path / "evidence",
        perform_real_venue_post=True,
        k1_backend=_FakeKeychainBackend(),
        opener_factory=lambda: _TimeoutOpener(),
        read_only_get_transport=PilotGuardReadTransport(),
        execution_integrity_backend=MockCurrentProductive29PIntegrityBackendV1(
            origin_main=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            head=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            drift="",
        ),
    )
    assert result.post_outcome == "UNKNOWN_EXTERNAL_EFFECT_POSSIBLE"


def test_second_new_risk_post_blocked_after_unknown_submit(tmp_path: Path) -> None:
    envelope = _envelope()
    kwargs = mandatory_new_risk_execute_kwargs(tmp_path)
    execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
        owner_go=OWNER_GO,
        baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        envelope=envelope,
        store_root=tmp_path,
        evidence_root=tmp_path / "evidence",
        perform_real_venue_post=True,
        k1_backend=_FakeKeychainBackend(),
        opener_factory=lambda: _TimeoutOpener(),
        read_only_get_transport=PilotGuardReadTransport(avail_eq="10000"),
        execution_integrity_backend=MockCurrentProductive29PIntegrityBackendV1(
            origin_main=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            head=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            drift="",
        ),
        **kwargs,
    )
    plan2 = VenuePlanCandidateV1(
        instrument_id="okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap",
        side="buy",
        quantity="1",
        order_type="market",
        td_mode="cross",
        reduce_only=False,
        clordid="pt-pilot-second-entry-v1",
        venue_native_payload={
            "instId": INST,
            "ordType": "market",
            "side": "buy",
            "sz": "1",
            "tdMode": "cross",
        },
        quantity_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        side_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        instrument_source="DH_CAP24_BOUND_INSTRUMENT_ID",
        path_kind="FULL_CORE_CURRENT_PRODUCTIVE",
    )
    envelope2 = bind_final_order_envelope_from_venue_plan_v1(
        plan2,
        admission_ref="TEST_ADMISSION_REF",
        provenance_ref="TEST_PROVENANCE_REF",
        creation_epoch="2026-10-14T00:00:01Z",
    )
    with pytest.raises(
        CurrentProductiveActualVenuePostError,
        match="NO_NEW_ENTRY_WHILE_UNKNOWN",
    ):
        execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
            owner_go=OWNER_GO,
            baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            envelope=envelope2,
            store_root=tmp_path,
            evidence_root=tmp_path / "evidence2",
            perform_real_venue_post=True,
            k1_backend=_FakeKeychainBackend(),
            opener_factory=lambda: _TimeoutOpener(),
            read_only_get_transport=PilotGuardReadTransport(avail_eq="10000"),
            execution_integrity_backend=MockCurrentProductive29PIntegrityBackendV1(
                origin_main=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                head=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                drift="",
            ),
            **kwargs,
        )


def test_config_digest_mismatch_blocks(tmp_path: Path) -> None:
    from tests.ops.test_full_core_pre_post_capital_guard_join_v1 import (
        _clean_exposure,
        _clean_margin,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_binding_v1 import (
        FullCoreCapitalGuardInstrumentMetadataV1,
        build_full_core_enter_post_capital_guard_join_binding_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
        DISPOSITION_PRE_EXTERNAL_EFFECT,
    )

    envelope = _envelope()
    cfg = _ratified_cfg()
    meta = FullCoreCapitalGuardInstrumentMetadataV1(ct_val="1", min_sz="1", lot_sz="1")
    b = build_full_core_enter_post_capital_guard_join_binding_v1(
        canonical_decision_id="dec-digest",
        native_instrument_id=INST,
        envelope=envelope,
        master_v2_decision="enter_long",
        account_identity=ACCOUNT_UID,
        environment="PRODUCTIVE_READ_ONLY",
        origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        guard_config_digest="deadbeef00000000000000000000000000000000000000000000000000000000",
        instrument_metadata=meta,
        terminal_disposition=DISPOSITION_PRE_EXTERNAL_EFFECT,
    )
    result = run_full_core_pre_post_capital_guard_join_v1(
        binding=b,
        envelope=envelope,
        guard_config=cfg,
        join_mode=FullCoreCapitalGuardJoinMode.PRODUCTIVE_PILOT_ENFORCE,
        pilot_enforce_owner_go=OWNER_GO_CURRENT_PILOT_CAPITAL_GUARD_POST_BIND_V1,
        margin_evidence=_clean_margin(),
        exposure_evidence=_clean_exposure(),
        atomic_state_dir=tmp_path,
        pretrade_reference_mark_px="10.0",
    )
    assert result.guard_blocked is True
    assert "GUARD_CONFIG_DIGEST_MISMATCH" in result.reasons


def test_adversarial_manual_reduce_only_without_provenance_blocked(tmp_path: Path) -> None:
    envelope = _manual_reduce_only_envelope()
    with pytest.raises(
        CurrentProductiveActualVenuePostError,
        match="RISK_REDUCING_.*PROVENANCE",
    ):
        execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
            owner_go=OWNER_GO,
            baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            envelope=envelope,
            store_root=tmp_path,
            evidence_root=tmp_path / "evidence",
            perform_real_venue_post=True,
            k1_backend=_FakeKeychainBackend(),
            opener_factory=lambda: _TimeoutOpener(),
            read_only_get_transport=PilotGuardReadTransport(),
            execution_integrity_backend=MockCurrentProductive29PIntegrityBackendV1(
                origin_main=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                head=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                drift="",
            ),
        )


def test_adversarial_forged_flatten_provenance_blocked() -> None:
    plan = VenuePlanCandidateV1(
        instrument_id="okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap",
        side="sell",
        quantity="1",
        order_type="limit",
        td_mode="cross",
        reduce_only=True,
        clordid="pt-forged-flatten-v1",
        venue_native_payload={
            "instId": INST,
            "ordType": "limit",
            "side": "sell",
            "sz": "1",
            "tdMode": "cross",
            "reduceOnly": True,
            "px": "10.0",
        },
        quantity_source=EXACT_OBJECT_FLATTEN_QUANTITY_SOURCE,
        side_source=EXACT_OBJECT_FLATTEN_SIDE_SOURCE,
        instrument_source=EXACT_OBJECT_FLATTEN_INSTRUMENT_SOURCE,
        path_kind="FULL_CORE_CURRENT_PRODUCTIVE",
    )
    envelope = bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref=EXACT_OBJECT_FLATTEN_ADMISSION_REF,
        provenance_ref=EXACT_OBJECT_FLATTEN_PROVENANCE_REF,
        creation_epoch="2026-10-14T00:00:00Z",
    )
    with pytest.raises(RiskReducingEnvelopeProvenanceError, match="NOT_AUTHORIZED"):
        classify_productive_venue_post_risk_class_v1(envelope)


def test_adversarial_valid_digest_invalid_provenance_blocked() -> None:
    envelope = _manual_reduce_only_envelope()
    assert envelope.envelope_digest
    with pytest.raises(RiskReducingEnvelopeProvenanceError):
        classify_productive_venue_post_risk_class_v1(envelope)


def test_adversarial_verified_flatten_plan_classifies_risk_reducing() -> None:
    envelope = _authorized_exact_object_flatten_envelope()
    assert (
        classify_productive_venue_post_risk_class_v1(envelope)
        is ProductiveVenuePostRiskClassV1.RISK_REDUCING
    )


def test_adversarial_post_payload_reduce_only_mismatch_blocked() -> None:
    envelope = _authorized_exact_object_flatten_envelope(clordid="pt-payload-bind-v1")
    with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match="POST_PAYLOAD_REDUCE_ONLY_MISMATCH"):
        assert_post_payload_reduce_only_matches_envelope_v1(envelope, {"reduceOnly": False})


def test_adversarial_new_risk_still_mandatory_guard(tmp_path: Path) -> None:
    envelope = _envelope()
    with pytest.raises(CurrentProductiveActualVenuePostError):
        execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
            owner_go=OWNER_GO,
            baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            envelope=envelope,
            store_root=tmp_path,
            evidence_root=tmp_path / "evidence",
            perform_real_venue_post=True,
            k1_backend=_FakeKeychainBackend(),
            opener_factory=lambda: _TimeoutOpener(),
            read_only_get_transport=PilotGuardReadTransport(avail_eq="10000"),
            execution_integrity_backend=MockCurrentProductive29PIntegrityBackendV1(
                origin_main=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                head=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                drift="",
            ),
        )


def test_adversarial_missing_provenance_identity_blocked() -> None:
    plan = VenuePlanCandidateV1(
        instrument_id="okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap",
        side="sell",
        quantity="1",
        order_type="market",
        td_mode="cross",
        reduce_only=True,
        clordid="pt-missing-id-v1",
        venue_native_payload={
            "instId": INST,
            "ordType": "market",
            "side": "sell",
            "sz": "1",
            "tdMode": "cross",
            "reduceOnly": True,
        },
        quantity_source="",
        side_source=EXACT_OBJECT_FLATTEN_SIDE_SOURCE,
        instrument_source=EXACT_OBJECT_FLATTEN_INSTRUMENT_SOURCE,
        path_kind=PATH_KIND_EXACT_OBJECT_FLATTEN,
    )
    with pytest.raises(FullCoreFinalOrderEnvelopeError, match="QUANTITY_SOURCE_MISSING"):
        bind_final_order_envelope_from_venue_plan_v1(
            plan,
            admission_ref=EXACT_OBJECT_FLATTEN_ADMISSION_REF,
            provenance_ref=EXACT_OBJECT_FLATTEN_PROVENANCE_REF,
            creation_epoch="2026-10-14T00:00:00Z",
        )


def test_adversarial_authorized_exit_uses_own_contract_not_entry_bypass(tmp_path: Path) -> None:
    envelope = _authorized_exact_object_flatten_envelope(clordid="pt-exit-own-contract-v1")
    result = execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
        owner_go=OWNER_GO,
        baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        envelope=envelope,
        store_root=tmp_path,
        evidence_root=tmp_path / "evidence",
        perform_real_venue_post=True,
        k1_backend=_FakeKeychainBackend(),
        opener_factory=lambda: _TimeoutOpener(),
        read_only_get_transport=PilotGuardReadTransport(),
        execution_integrity_backend=MockCurrentProductive29PIntegrityBackendV1(
            origin_main=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            head=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            drift="",
        ),
    )
    assert result.post_outcome == "UNKNOWN_EXTERNAL_EFFECT_POSSIBLE"
