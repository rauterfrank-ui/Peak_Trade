"""Offline regression matrix for recovery guard exposure signal derivation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
    FullCoreAuthorizationBindingV1,
    full_core_atomic_mark_submit_boundary_v1,
    full_core_atomic_reserve_owner_go_authorization_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_join_v1 import (
    FullCoreCapitalGuardJoinMode,
    run_full_core_pre_post_capital_guard_join_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_recovery_guard_exposure_signals_v1 import (
    compose_capital_guard_exposure_evidence_v1,
    derive_full_core_recovery_guard_exposure_signals_v1,
    merge_recovery_guard_exposure_evidence_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.canary_capital_guard_atomic_one_shot_v1 import (
    STATE_HALTED_UNRESOLVED,
    STATE_RECONCILIATION_PENDING,
    STATE_SCHEMA_VERSION,
    STATE_SUBMIT_MAY_HAVE_OCCURRED,
    STATE_TERMINAL_RECONCILED,
    _paths,
)
from tests.ops.test_full_core_pre_post_capital_guard_join_v1 import (
    _binding,
    _clean_exposure,
    _clean_margin,
    _envelope,
)


def _auth_binding(**overrides: str) -> FullCoreAuthorizationBindingV1:
    base = dict(
        owner_go="OWNER_GO_FULL_CORE_PRE_POST",
        origin_main_sha="38d607a43aa38683cb21158aa96703866fb0a2ac",
        account_scope="acct-recovery-guard-1",
        environment="OFFLINE_STUB",
        execution_mode="OFFLINE_STUB",
        canonical_decision_id="dec-recovery-1",
        instrument_id="0G-USDT-SWAP",
        native_id="0G-USDT-SWAP",
        selected_direction="ENTER_LONG",
        order_side="buy",
        final_quantity="1",
        order_type="limit",
        order_price="10",
        venue_plan_digest="venue-digest-1",
        envelope_digest="env-digest-1",
        guard_config_digest="cfg-digest-1",
        session_id="sess-1",
        clordid="pt-recovery-guard-1",
    )
    base.update(overrides)
    return FullCoreAuthorizationBindingV1(**base)


def _write_atomic_state(
    *,
    state_dir: Path,
    consumption_key: str,
    state: str,
    binding_digest: str,
    binding: dict[str, str],
) -> None:
    state_path, _ = _paths(state_dir, consumption_key)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": STATE_SCHEMA_VERSION,
        "consumption_key": consumption_key,
        "state": state,
        "binding_digest": binding_digest,
        "binding": binding,
        "authorization_permanently_consumed": True,
    }
    state_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def test_missing_exposure_evidence_uses_atomic_available_without_false_halt(
    tmp_path: Path,
) -> None:
    auth = _auth_binding()
    signals = derive_full_core_recovery_guard_exposure_signals_v1(
        state_dir=tmp_path,
        consumption_key=auth.consumption_key(),
    )
    exposure = compose_capital_guard_exposure_evidence_v1(
        exposure_evidence=None,
        atomic_signals=signals,
    )
    assert exposure.recovery_state_clear is True
    assert exposure.unknown_submit_active is False


def test_terminal_recovery_clear_independent_of_entry_slot(tmp_path: Path) -> None:
    from src.ops.full_core_live_path_composition_root_v1.current_full_core_capital_guard_v1 import (
        ratified_offline_full_core_guard_config_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_join_v1 import (
        _authorization_binding_v1,
    )

    env = _envelope()
    b = _binding(env)
    join_auth = _authorization_binding_v1(b, session_id="full-core-capital-guard-join")
    _write_atomic_state(
        state_dir=tmp_path,
        consumption_key=join_auth.consumption_key(),
        state=STATE_TERMINAL_RECONCILED,
        binding_digest=join_auth.to_canary_atomic_binding_v1().binding_digest(),
        binding={"instrument_id": join_auth.instrument_id, "clordid": join_auth.clordid},
    )
    result = run_full_core_pre_post_capital_guard_join_v1(
        binding=b,
        envelope=env,
        guard_config=ratified_offline_full_core_guard_config_v1(),
        join_mode=FullCoreCapitalGuardJoinMode.OFFLINE_STUB,
        margin_evidence=_clean_margin(),
        exposure_evidence=_clean_exposure(recovery_state_clear=True),
        atomic_state_dir=tmp_path,
        observed_leverage="5",
    )
    assert result.guard_blocked is True
    assert any(
        "DURABLE_ENTRY_SLOT_UNAVAILABLE" in r or "OWNER_GO_ALREADY_CONSUMED" in r
        for r in result.reasons
    )


def test_case_01_available_no_unknown(tmp_path: Path) -> None:
    auth = _auth_binding()
    signals = derive_full_core_recovery_guard_exposure_signals_v1(
        state_dir=tmp_path,
        consumption_key=auth.consumption_key(),
    )
    assert signals.unknown_submit_active is False
    assert signals.recovery_state_clear is True


def test_case_02_submit_may_have_occurred_flat_exchange_flags(tmp_path: Path) -> None:
    auth = _auth_binding()
    tmp = tmp_path
    full_core_atomic_reserve_owner_go_authorization_v1(state_dir=tmp, binding=auth)
    full_core_atomic_mark_submit_boundary_v1(state_dir=tmp, binding=auth)
    signals = derive_full_core_recovery_guard_exposure_signals_v1(
        state_dir=tmp,
        consumption_key=auth.consumption_key(),
        expected_binding_digest=auth.to_canary_atomic_binding_v1().binding_digest(),
    )
    assert signals.durable_atomic_state == STATE_SUBMIT_MAY_HAVE_OCCURRED
    assert signals.unknown_submit_active is True
    assert signals.recovery_state_clear is False
    exposure = merge_recovery_guard_exposure_evidence_v1(
        exposure_evidence=_clean_exposure(recovery_state_clear=True),
        atomic_signals=signals,
    )
    assert exposure.recovery_state_clear is False
    assert exposure.unknown_submit_active is True


def test_case_03_halted_unresolved(tmp_path: Path) -> None:
    auth = _auth_binding()
    _write_atomic_state(
        state_dir=tmp_path,
        consumption_key=auth.consumption_key(),
        state=STATE_HALTED_UNRESOLVED,
        binding_digest=auth.to_canary_atomic_binding_v1().binding_digest(),
        binding={"instrument_id": auth.instrument_id, "clordid": auth.clordid},
    )
    signals = derive_full_core_recovery_guard_exposure_signals_v1(
        state_dir=tmp_path,
        consumption_key=auth.consumption_key(),
        expected_binding_digest=auth.to_canary_atomic_binding_v1().binding_digest(),
    )
    assert signals.recovery_state_clear is False
    assert signals.unknown_submit_active is True


def test_case_04_reconciliation_pending(tmp_path: Path) -> None:
    auth = _auth_binding()
    _write_atomic_state(
        state_dir=tmp_path,
        consumption_key=auth.consumption_key(),
        state=STATE_RECONCILIATION_PENDING,
        binding_digest=auth.to_canary_atomic_binding_v1().binding_digest(),
        binding={"instrument_id": auth.instrument_id, "clordid": auth.clordid},
    )
    signals = derive_full_core_recovery_guard_exposure_signals_v1(
        state_dir=tmp_path,
        consumption_key=auth.consumption_key(),
        expected_binding_digest=auth.to_canary_atomic_binding_v1().binding_digest(),
    )
    assert signals.recovery_state_clear is False
    assert signals.unknown_submit_active is False


def test_case_05_terminal_reconciled(tmp_path: Path) -> None:
    auth = _auth_binding()
    _write_atomic_state(
        state_dir=tmp_path,
        consumption_key=auth.consumption_key(),
        state=STATE_TERMINAL_RECONCILED,
        binding_digest=auth.to_canary_atomic_binding_v1().binding_digest(),
        binding={"instrument_id": auth.instrument_id, "clordid": auth.clordid},
    )
    signals = derive_full_core_recovery_guard_exposure_signals_v1(
        state_dir=tmp_path,
        consumption_key=auth.consumption_key(),
        expected_binding_digest=auth.to_canary_atomic_binding_v1().binding_digest(),
    )
    assert signals.recovery_state_clear is True
    assert signals.unknown_submit_active is False


def test_case_07_corrupt_ledger_fail_closed(tmp_path: Path) -> None:
    auth = _auth_binding()
    state_path, _ = _paths(tmp_path, auth.consumption_key())
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text("{not-json", encoding="utf-8")
    signals = derive_full_core_recovery_guard_exposure_signals_v1(
        state_dir=tmp_path,
        consumption_key=auth.consumption_key(),
    )
    assert signals.recovery_state_clear is False
    assert signals.unknown_submit_active is True


def test_case_08_binding_digest_mismatch(tmp_path: Path) -> None:
    auth = _auth_binding()
    _write_atomic_state(
        state_dir=tmp_path,
        consumption_key=auth.consumption_key(),
        state=STATE_TERMINAL_RECONCILED,
        binding_digest="deadbeef",
        binding={"instrument_id": auth.instrument_id, "clordid": auth.clordid},
    )
    signals = derive_full_core_recovery_guard_exposure_signals_v1(
        state_dir=tmp_path,
        consumption_key=auth.consumption_key(),
        expected_binding_digest=auth.to_canary_atomic_binding_v1().binding_digest(),
    )
    assert signals.recovery_state_clear is False
    assert signals.unknown_submit_active is True


def test_join_blocks_unknown_atomic_with_flat_exposure_evidence(tmp_path: Path) -> None:
    from src.ops.full_core_live_path_composition_root_v1.current_full_core_capital_guard_v1 import (
        ratified_offline_full_core_guard_config_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_join_v1 import (
        _authorization_binding_v1,
    )

    env = _envelope()
    b = _binding(env)
    join_auth = _authorization_binding_v1(b, session_id="full-core-capital-guard-join")
    _write_atomic_state(
        state_dir=tmp_path,
        consumption_key=join_auth.consumption_key(),
        state=STATE_SUBMIT_MAY_HAVE_OCCURRED,
        binding_digest=join_auth.to_canary_atomic_binding_v1().binding_digest(),
        binding={"instrument_id": join_auth.instrument_id, "clordid": join_auth.clordid},
    )
    result = run_full_core_pre_post_capital_guard_join_v1(
        binding=b,
        envelope=env,
        guard_config=ratified_offline_full_core_guard_config_v1(),
        join_mode=FullCoreCapitalGuardJoinMode.OFFLINE_STUB,
        margin_evidence=_clean_margin(),
        exposure_evidence=_clean_exposure(recovery_state_clear=True),
        atomic_state_dir=tmp_path,
        observed_leverage="5",
    )
    assert result.guard_blocked is True
    assert "UNKNOWN_SUBMIT_ACTIVE" in result.reasons or "RECOVERY_STATE_UNCLEAR" in result.reasons
