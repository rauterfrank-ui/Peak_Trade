"""Offline proofs for CURRENT_LIVE_CANARY_CAPITAL_GUARD_V1."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    OWNER_GO_EXECUTE,
    REUSED_BINDING_ACCOUNT_SCOPE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.current_live_canary_capital_guard_v1 import (
    CanaryCapitalGuardError,
    CanaryCapitalGuardExposureEvidenceV1,
    CanaryCapitalGuardMarginEvidenceV1,
    CanaryCapitalGuardSessionV1,
    IMR_SOURCE_PUBLIC_POSITION_TIERS_QTY_ONE,
    build_default_guard_session_v1,
    compute_order_notional_usdc_v1,
    evaluate_canary_capital_guard_entry_v1,
    evaluate_canary_capital_guard_flatten_v1,
    load_canary_capital_guard_config_v1,
    offline_proof_guard_config_v1,
    parse_canary_capital_guard_config_v1,
    record_canary_capital_guard_entry_attempt_v1,
    refuse_canary_capital_guard_entry_unless_pass_v1,
    refuse_canary_capital_guard_flatten_unless_pass_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.ghv_canary_capital_guard_observability_v1 import (
    STAGE_CANARY_CAPITAL_GUARD_DECISION,
    build_canary_capital_guard_ghv_bundle_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    CanaryFlattenOrderPlanV1,
    CanaryOrderPlanV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _sample_plan(
    *,
    quantity: str = "1",
    max_notional: str = "10",
    limit_price: str = "10",
) -> CanaryOrderPlanV1:
    return CanaryOrderPlanV1(
        instrument_id=DEFAULT_INSTRUMENT_ID,
        side="BUY",
        order_type="LIMIT",
        td_mode="cross",
        quantity=quantity,
        quantity_domain="VENUE_CONTRACT_COUNT",
        quantity_unit="contracts",
        limit_price=limit_price,
        min_sz="1",
        lot_sz="1",
        tick_sz="0.0001",
        ct_val="1",
        ct_val_ccy="USDC",
        min_executable_notional=max_notional,
        max_notional=max_notional,
        clordid="ptcanarytest0001",
        venue_native_payload={"instId": DEFAULT_INSTRUMENT_ID, "sz": quantity, "side": "buy"},
    )


def _clean_exposure(**overrides: object) -> CanaryCapitalGuardExposureEvidenceV1:
    base = dict(
        open_order_count=0,
        open_position_count=0,
        unknown_submit_active=False,
        recovery_state_clear=True,
        transport_retry_count=0,
    )
    base.update(overrides)
    return CanaryCapitalGuardExposureEvidenceV1(**base)  # type: ignore[arg-type]


def _clean_margin(**overrides: object) -> CanaryCapitalGuardMarginEvidenceV1:
    base = dict(
        avail_eq_usdc="1000",
        imr_rate="0.05",
        imr_source_class=IMR_SOURCE_PUBLIC_POSITION_TIERS_QTY_ONE,
        pretrade_decision_id="pt-1",
        expected_pretrade_decision_id="pt-1",
    )
    base.update(overrides)
    return CanaryCapitalGuardMarginEvidenceV1(**base)  # type: ignore[arg-type]


def _ratified_offline_config():
    return replace(offline_proof_guard_config_v1(), owner_caps_ratified=True)


def _session(cfg) -> CanaryCapitalGuardSessionV1:
    return build_default_guard_session_v1(
        session_id="sess-proof-1",
        instrument_id=DEFAULT_INSTRUMENT_ID,
        owner_go=OWNER_GO_EXECUTE,
        guard_config=cfg,
    )


def test_default_repo_config_blocks_live_canary() -> None:
    cfg = load_canary_capital_guard_config_v1(repo_root=REPO_ROOT)
    assert cfg.live_canary_allowed is False
    assert cfg.owner_caps_ratified is False
    ev = evaluate_canary_capital_guard_entry_v1(
        plan=_sample_plan(),
        guard_config=cfg,
        margin_evidence=_clean_margin(),
        exposure_evidence=_clean_exposure(),
        owner_go=OWNER_GO_EXECUTE,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        session=_session(cfg),
        observed_leverage="5",
    )
    assert ev.guard_allowed is False
    assert "LIVE_CANARY_ALLOWED_FALSE" in ev.reasons
    assert "OWNER_CAPS_UNRATIFIED" in ev.reasons


def test_missing_caps_block() -> None:
    cfg = load_canary_capital_guard_config_v1(repo_root=REPO_ROOT)
    ev = evaluate_canary_capital_guard_entry_v1(
        plan=_sample_plan(),
        guard_config=cfg,
        margin_evidence=_clean_margin(),
        exposure_evidence=_clean_exposure(),
        owner_go=OWNER_GO_EXECUTE,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        session=_session(cfg),
        observed_leverage="5",
    )
    assert any(r.startswith("MISSING_NUMERIC_CAP:") for r in ev.reasons)


def test_excessive_notional_blocks_when_ratified() -> None:
    cfg = _ratified_offline_config()
    plan = _sample_plan(max_notional="500", limit_price="500")
    ev = evaluate_canary_capital_guard_entry_v1(
        plan=plan,
        guard_config=cfg,
        margin_evidence=_clean_margin(),
        exposure_evidence=_clean_exposure(),
        owner_go=OWNER_GO_EXECUTE,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        session=_session(cfg),
        observed_leverage="5",
    )
    assert "MAX_SINGLE_ORDER_NOTIONAL_EXCEEDED" in ev.reasons


def test_excessive_leverage_blocks() -> None:
    cfg = _ratified_offline_config()
    ev = evaluate_canary_capital_guard_entry_v1(
        plan=_sample_plan(),
        guard_config=cfg,
        margin_evidence=_clean_margin(),
        exposure_evidence=_clean_exposure(),
        owner_go=OWNER_GO_EXECUTE,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        session=_session(cfg),
        observed_leverage="50",
    )
    assert "MAX_LEVERAGE_EXCEEDED" in ev.reasons


def test_quantity_mismatch_scale_in_blocks() -> None:
    cfg = _ratified_offline_config()
    ev = evaluate_canary_capital_guard_entry_v1(
        plan=_sample_plan(quantity="2"),
        guard_config=cfg,
        margin_evidence=_clean_margin(),
        exposure_evidence=_clean_exposure(),
        owner_go=OWNER_GO_EXECUTE,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        session=_session(cfg),
        observed_leverage="5",
    )
    assert "SCALE_IN_FORBIDDEN" in ev.reasons


def test_missing_imr_blocks() -> None:
    cfg = _ratified_offline_config()
    ev = evaluate_canary_capital_guard_entry_v1(
        plan=_sample_plan(),
        guard_config=cfg,
        margin_evidence=_clean_margin(imr_rate=None),
        exposure_evidence=_clean_exposure(),
        owner_go=OWNER_GO_EXECUTE,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        session=_session(cfg),
        observed_leverage="5",
    )
    assert "MISSING_IMR_EVIDENCE" in ev.reasons


def test_missing_exposure_margin_blocks() -> None:
    cfg = _ratified_offline_config()
    ev = evaluate_canary_capital_guard_entry_v1(
        plan=_sample_plan(),
        guard_config=cfg,
        margin_evidence=_clean_margin(avail_eq_usdc=None),
        exposure_evidence=_clean_exposure(),
        owner_go=OWNER_GO_EXECUTE,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        session=_session(cfg),
        observed_leverage="5",
    )
    assert "MISSING_AVAILABLE_MARGIN_EVIDENCE" in ev.reasons


def test_existing_position_and_order_block() -> None:
    cfg = _ratified_offline_config()
    ev_pos = evaluate_canary_capital_guard_entry_v1(
        plan=_sample_plan(),
        guard_config=cfg,
        margin_evidence=_clean_margin(),
        exposure_evidence=_clean_exposure(open_position_count=1),
        owner_go=OWNER_GO_EXECUTE,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        session=_session(cfg),
        observed_leverage="5",
    )
    assert "OPEN_POSITION_PRESENT" in ev_pos.reasons
    ev_ord = evaluate_canary_capital_guard_entry_v1(
        plan=_sample_plan(),
        guard_config=cfg,
        margin_evidence=_clean_margin(),
        exposure_evidence=_clean_exposure(open_order_count=1),
        owner_go=OWNER_GO_EXECUTE,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        session=_session(cfg),
        observed_leverage="5",
    )
    assert "OPEN_ORDER_PRESENT" in ev_ord.reasons


def test_unknown_submit_and_duplicate_block() -> None:
    cfg = _ratified_offline_config()
    session = _session(cfg)
    plan = _sample_plan()
    digest = evaluate_canary_capital_guard_entry_v1(
        plan=plan,
        guard_config=cfg,
        margin_evidence=_clean_margin(),
        exposure_evidence=_clean_exposure(),
        owner_go=OWNER_GO_EXECUTE,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        session=session,
        observed_leverage="5",
    ).plan_digest
    session = record_canary_capital_guard_entry_attempt_v1(session=session, plan_digest=digest)
    ev = evaluate_canary_capital_guard_entry_v1(
        plan=plan,
        guard_config=cfg,
        margin_evidence=_clean_margin(),
        exposure_evidence=_clean_exposure(unknown_submit_active=True),
        owner_go=OWNER_GO_EXECUTE,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        session=session,
        observed_leverage="5",
    )
    assert "UNKNOWN_SUBMIT_ACTIVE" in ev.reasons
    ev_dup = evaluate_canary_capital_guard_entry_v1(
        plan=plan,
        guard_config=cfg,
        margin_evidence=_clean_margin(),
        exposure_evidence=_clean_exposure(),
        owner_go=OWNER_GO_EXECUTE,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        session=session,
        observed_leverage="5",
    )
    assert "DUPLICATE_PLAN_DIGEST" in ev_dup.reasons or "MAX_NEW_ORDERS_EXCEEDED" in ev_dup.reasons


def test_missing_owner_permit_blocks() -> None:
    cfg = _ratified_offline_config()
    ev = evaluate_canary_capital_guard_entry_v1(
        plan=_sample_plan(),
        guard_config=cfg,
        margin_evidence=_clean_margin(),
        exposure_evidence=_clean_exposure(),
        owner_go=None,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        session=_session(cfg),
        observed_leverage="5",
    )
    assert "OWNER_PERMIT_MISSING" in ev.reasons


def test_pass_when_ratified_and_within_caps() -> None:
    cfg = _ratified_offline_config()
    ev = evaluate_canary_capital_guard_entry_v1(
        plan=_sample_plan(max_notional="50"),
        guard_config=cfg,
        margin_evidence=_clean_margin(avail_eq_usdc="1000"),
        exposure_evidence=_clean_exposure(),
        owner_go=OWNER_GO_EXECUTE,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        session=_session(cfg),
        observed_leverage="5",
    )
    assert ev.guard_allowed is True
    refuse_canary_capital_guard_entry_unless_pass_v1(ev)


def test_notional_decimal_formula() -> None:
    value = compute_order_notional_usdc_v1(quantity="1", contract_value="1", reference_price="10.5")
    assert value == Decimal("10.5")


def test_flatten_cannot_increase_exposure() -> None:
    plan = CanaryFlattenOrderPlanV1(
        instrument_id=DEFAULT_INSTRUMENT_ID,
        side="SELL",
        order_type="limit",
        td_mode="cross",
        quantity="5",
        reduce_only=True,
        clordid="ptcanaryflat001",
        limit_price=None,
        price_gate_status="UNPRICED",
        venue_native_payload=None,
        submitted_entry_sz_used=False,
    )
    ev = evaluate_canary_capital_guard_flatten_v1(
        plan=plan,
        signed_pos=Decimal("2"),
        reduce_only_confirmed=True,
    )
    assert "FLATTEN_EXCEEDS_OBSERVED_POSITION" in ev.reasons
    with pytest.raises(CanaryCapitalGuardError):
        refuse_canary_capital_guard_flatten_unless_pass_v1(ev)


def test_ghv_stages_recorded() -> None:
    cfg = _ratified_offline_config()
    ev = evaluate_canary_capital_guard_entry_v1(
        plan=_sample_plan(max_notional="50"),
        guard_config=cfg,
        margin_evidence=_clean_margin(),
        exposure_evidence=_clean_exposure(),
        owner_go=OWNER_GO_EXECUTE,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        session=_session(cfg),
        observed_leverage="5",
    )
    bundle = build_canary_capital_guard_ghv_bundle_v1(
        session_id="sess-ghv",
        guard_config=cfg.to_dict(),
        guard_input={"test": True},
        evaluation=ev,
    )
    stages = {row["stage"] for row in bundle["ghv_canary_capital_guard_stages"]}
    assert STAGE_CANARY_CAPITAL_GUARD_DECISION in stages


def _minimal_guard_config_payload(**overrides: object) -> dict:
    base = {
        "schema_version": "current_live_canary_capital_guard.v1",
        "live_canary_allowed": False,
        "owner_caps_ratified": False,
        "currency": "USDC",
        "max_new_orders": 1,
        "max_new_positions": 1,
    }
    base.update(overrides)
    return base


def test_max_new_orders_zero_entry_blocked() -> None:
    cfg = replace(_ratified_offline_config(), max_new_orders=0)
    ev = evaluate_canary_capital_guard_entry_v1(
        plan=_sample_plan(max_notional="50"),
        guard_config=cfg,
        margin_evidence=_clean_margin(avail_eq_usdc="1000"),
        exposure_evidence=_clean_exposure(),
        owner_go=OWNER_GO_EXECUTE,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        session=_session(cfg),
        observed_leverage="5",
    )
    assert "ENTRY_BLOCKED:MAX_NEW_ORDERS_ZERO" in ev.reasons
    assert ev.guard_allowed is False


def test_max_new_positions_zero_entry_blocked() -> None:
    cfg = replace(_ratified_offline_config(), max_new_positions=0)
    ev = evaluate_canary_capital_guard_entry_v1(
        plan=_sample_plan(max_notional="50"),
        guard_config=cfg,
        margin_evidence=_clean_margin(avail_eq_usdc="1000"),
        exposure_evidence=_clean_exposure(),
        owner_go=OWNER_GO_EXECUTE,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        session=_session(cfg),
        observed_leverage="5",
    )
    assert "ENTRY_BLOCKED:MAX_NEW_POSITIONS_ZERO" in ev.reasons
    assert ev.guard_allowed is False


def test_parse_missing_max_new_orders_cap_blocks() -> None:
    payload = _minimal_guard_config_payload()
    del payload["max_new_orders"]
    with pytest.raises(CanaryCapitalGuardError, match="MISSING_INT_CAP:max_new_orders"):
        parse_canary_capital_guard_config_v1(payload, config_digest="test")


def test_parse_invalid_max_new_orders_cap_blocks() -> None:
    payload = _minimal_guard_config_payload(max_new_orders=-1)
    with pytest.raises(CanaryCapitalGuardError, match="NEGATIVE_INT_CAP:max_new_orders"):
        parse_canary_capital_guard_config_v1(payload, config_digest="test")
    payload2 = _minimal_guard_config_payload(max_new_orders="not-an-int")
    with pytest.raises(CanaryCapitalGuardError, match="INVALID_INT_CAP:max_new_orders"):
        parse_canary_capital_guard_config_v1(payload2, config_digest="test")


def test_parse_explicit_zero_preserved_not_coerced_to_one() -> None:
    payload = _minimal_guard_config_payload(max_new_orders=0, max_new_positions=0)
    cfg = parse_canary_capital_guard_config_v1(payload, config_digest="test")
    assert cfg.max_new_orders == 0
    assert cfg.max_new_positions == 0


def test_positive_ratified_int_caps_evaluated_normally() -> None:
    cfg = replace(_ratified_offline_config(), max_new_orders=2, max_new_positions=2)
    ev = evaluate_canary_capital_guard_entry_v1(
        plan=_sample_plan(max_notional="50"),
        guard_config=cfg,
        margin_evidence=_clean_margin(avail_eq_usdc="1000"),
        exposure_evidence=_clean_exposure(),
        owner_go=OWNER_GO_EXECUTE,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        session=_session(cfg),
        observed_leverage="5",
    )
    assert ev.guard_allowed is True
    assert "ENTRY_BLOCKED:MAX_NEW_ORDERS_ZERO" not in ev.reasons
    assert "ENTRY_BLOCKED:MAX_NEW_POSITIONS_ZERO" not in ev.reasons


def test_submit_transport_wires_capital_guard_before_post() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1 import submit_transport_v1

    src = Path(submit_transport_v1.__file__).read_text(encoding="utf-8")
    assert "_evaluate_and_refuse_entry_capital_guard_v1" in src
    guard_idx = src.index("_evaluate_and_refuse_entry_capital_guard_v1(")
    gate_idx = src.index("refuse_submit_unless_gates_pass_v1(submit_gate)")
    # Use the call site inside run_canary_submit_transport, not the helper definition.
    guard_idx = src.index("capital_guard_config=resolved_guard_config", guard_idx)
    assert guard_idx < gate_idx
