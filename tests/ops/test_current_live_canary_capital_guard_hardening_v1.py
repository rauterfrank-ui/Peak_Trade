"""Hardening proofs for CURRENT_LIVE_CANARY_CAPITAL_GUARD_V1."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.canary_capital_guard_durable_ledger_v1 import (
    CanaryCapitalGuardDurableLedgerError,
    assert_durable_entry_slot_available_v1,
    compute_canary_owner_scope_key_v1,
    record_durable_entry_reservation_v1,
    record_durable_unknown_submit_v1,
    resolve_durable_slot_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    OWNER_GO_EXECUTE,
    REUSED_BINDING_ACCOUNT_SCOPE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.current_live_canary_capital_guard_v1 import (
    CanaryCapitalGuardExposureEvidenceV1,
    CanaryCapitalGuardMarginEvidenceV1,
    IMR_SOURCE_PUBLIC_POSITION_TIERS_QTY_ONE,
    evaluate_canary_capital_guard_entry_v1,
    offline_proof_guard_config_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.cover_usdc_current_public_tier_mmr_productive_evidence_v1 import (
    encode_fixture_position_tiers_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_transport_v1 import (
    run_canary_submit_transport_v1,
)
from tests.ops.test_current_live_canary_capital_guard_v1 import (
    _clean_exposure,
    _ratified_offline_config,
    _sample_plan,
    _session,
)


def test_imr_source_not_authoritative_blocks() -> None:
    cfg = replace(_ratified_offline_config(), owner_caps_ratified=True)
    ev = evaluate_canary_capital_guard_entry_v1(
        plan=_sample_plan(max_notional="50"),
        guard_config=cfg,
        margin_evidence=CanaryCapitalGuardMarginEvidenceV1(
            avail_eq_usdc="1000",
            imr_rate="0.05",
            imr_source_class="INSTRUMENTS_METADATA",
            pretrade_decision_id="pt-1",
            expected_pretrade_decision_id="pt-1",
        ),
        exposure_evidence=_clean_exposure(),
        owner_go=OWNER_GO_EXECUTE,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        session=_session(cfg),
        observed_leverage="5",
        expected_config_digest=cfg.config_digest,
        durable_entry_state="AVAILABLE",
    )
    assert "IMR_SOURCE_NOT_AUTHORITATIVE" in ev.reasons


def test_stale_pretrade_margin_evidence_blocks() -> None:
    cfg = _ratified_offline_config()
    ev = evaluate_canary_capital_guard_entry_v1(
        plan=_sample_plan(max_notional="50"),
        guard_config=cfg,
        margin_evidence=CanaryCapitalGuardMarginEvidenceV1(
            avail_eq_usdc="1000",
            imr_rate="0.05",
            imr_source_class=IMR_SOURCE_PUBLIC_POSITION_TIERS_QTY_ONE,
            pretrade_decision_id="pt-old",
            expected_pretrade_decision_id="pt-new",
        ),
        exposure_evidence=_clean_exposure(),
        owner_go=OWNER_GO_EXECUTE,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        session=_session(cfg),
        observed_leverage="5",
        expected_config_digest=cfg.config_digest,
        durable_entry_state="AVAILABLE",
    )
    assert "STALE_MARGIN_EVIDENCE_PRETRADE_MISMATCH" in ev.reasons


def test_missing_fee_buffer_cap_blocks() -> None:
    cfg = replace(_ratified_offline_config(), fee_buffer_usdc=None)
    ev = evaluate_canary_capital_guard_entry_v1(
        plan=_sample_plan(max_notional="50"),
        guard_config=cfg,
        margin_evidence=CanaryCapitalGuardMarginEvidenceV1(
            avail_eq_usdc="1000",
            imr_rate="0.05",
            imr_source_class=IMR_SOURCE_PUBLIC_POSITION_TIERS_QTY_ONE,
            pretrade_decision_id="pt-1",
            expected_pretrade_decision_id="pt-1",
        ),
        exposure_evidence=_clean_exposure(),
        owner_go=OWNER_GO_EXECUTE,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        session=_session(cfg),
        observed_leverage="5",
        expected_config_digest=cfg.config_digest,
        durable_entry_state="AVAILABLE",
    )
    assert "MISSING_FEE_BUFFER_CAP" in ev.reasons


def test_durable_ledger_blocks_restart_duplicate(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    state_dir = tmp_path / "atomic"
    scope = compute_canary_owner_scope_key_v1(
        owner_go=OWNER_GO_EXECUTE,
        origin_main_sha="abc123",
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
    )
    assert_durable_entry_slot_available_v1(
        ledger_path=ledger, scope_key=scope, atomic_state_dir=state_dir
    )
    record_durable_entry_reservation_v1(
        ledger_path=ledger,
        scope_key=scope,
        plan_digest="plan-a",
        session_id="sess-a",
        guard_config_digest="cfg-a",
        owner_go=OWNER_GO_EXECUTE,
        origin_main_sha="abc123",
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        instrument_id="SUI-USDT-SWAP",
        clordid="cl-a",
        atomic_state_dir=state_dir,
    )
    slot = resolve_durable_slot_v1(ledger_path=ledger, scope_key=scope, atomic_state_dir=state_dir)
    assert slot.state == "RESERVED_PRE_POST"
    with pytest.raises(CanaryCapitalGuardDurableLedgerError):
        assert_durable_entry_slot_available_v1(
            ledger_path=ledger, scope_key=scope, atomic_state_dir=state_dir
        )


def test_unknown_submit_marks_durable_slot(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    state_dir = tmp_path / "atomic"
    scope = compute_canary_owner_scope_key_v1(
        owner_go=OWNER_GO_EXECUTE,
        origin_main_sha="abc123",
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
    )
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.canary_capital_guard_durable_ledger_v1 import (
        build_canary_authorization_binding_v1,
    )

    binding = build_canary_authorization_binding_v1(
        owner_go=OWNER_GO_EXECUTE,
        origin_main_sha="abc123",
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        environment="LIVE",
        instrument_id="SUI-USDT-SWAP",
        plan_digest="plan-a",
        guard_config_digest="cfg-a",
        session_id="sess-a",
        clordid="cl-a",
    )
    record_durable_entry_reservation_v1(
        ledger_path=ledger,
        scope_key=scope,
        plan_digest="plan-a",
        session_id="sess-a",
        guard_config_digest="cfg-a",
        owner_go=OWNER_GO_EXECUTE,
        origin_main_sha="abc123",
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        instrument_id="SUI-USDT-SWAP",
        clordid="cl-a",
        atomic_state_dir=state_dir,
    )
    record_durable_unknown_submit_v1(
        ledger_path=ledger,
        scope_key=scope,
        plan_digest="plan-a",
        binding=binding,
        atomic_state_dir=state_dir,
    )
    slot = resolve_durable_slot_v1(ledger_path=ledger, scope_key=scope, atomic_state_dir=state_dir)
    assert slot.state == "SUBMIT_MAY_HAVE_OCCURRED"


def test_guard_config_override_forbidden_by_default() -> None:
    src = Path(run_canary_submit_transport_v1.__code__.co_filename).read_text(encoding="utf-8")
    assert "GUARD_CONFIG_OVERRIDE_FORBIDDEN" in src


def test_public_position_tiers_fixture_imr_extracts() -> None:
    import json

    raw = encode_fixture_position_tiers_payload_v1(
        inst_family="SUI-USD_UM_XPERP",
        qty_one_imr="0.05",
        qty_one_mmr="0.004",
        qty_one_tier="1",
        qty_one_min_sz="1",
        qty_one_max_sz="100",
    )
    payload = json.loads(raw.decode("utf-8"))
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.current_live_canary_capital_guard_v1 import (
        bind_imr_from_public_position_tiers_payload_v1,
    )

    imr = bind_imr_from_public_position_tiers_payload_v1(
        position_tiers_payload=payload,
        expected_inst_family="SUI-USD_UM_XPERP",
    )
    assert Decimal(imr) == Decimal("0.05")
