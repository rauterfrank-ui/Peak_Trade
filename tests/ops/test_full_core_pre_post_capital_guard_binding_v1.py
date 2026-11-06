"""Binding producer proofs for productive PRE_EXTERNAL → Capital Guard."""

from __future__ import annotations

from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    build_final_order_envelope_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_binding_v1 import (
    FullCoreCapitalGuardInstrumentMetadataV1,
    build_full_core_capital_guard_join_binding_v1,
    compute_full_core_venue_plan_digest_from_envelope_v1,
)
from tests.ops.test_full_core_current_productive_pre_external_closure_v1 import _bound

_META = FullCoreCapitalGuardInstrumentMetadataV1(ct_val="1", min_sz="1", lot_sz="1")


def _envelope(side: str = "buy"):
    cl = "ptbindtest00000001"
    return build_final_order_envelope_v1(
        instrument_id="ADA-USDT-SWAP",
        side=side,
        order_type="limit",
        quantity="2",
        quantity_unit="CONTRACTS",
        td_mode="cross",
        reduce_only=False,
        client_order_id=cl,
        path_kind="ENTER",
        venue_plan_clordid=cl,
        quantity_source="FIXTURE",
        side_source="FIXTURE",
        instrument_source="FIXTURE",
        admission_ref="dec-epoch-1",
        provenance_ref="prov-1",
        creation_epoch="1700000000",
        price="1.5",
    )


def test_forward_reverse_envelope_digest_join() -> None:
    env = _envelope()
    d1 = compute_full_core_venue_plan_digest_from_envelope_v1(env)
    d2 = compute_full_core_venue_plan_digest_from_envelope_v1(env)
    assert d1 == d2
    binding = build_full_core_capital_guard_join_binding_v1(
        canonical_decision_id="dec-epoch-1",
        bound_instrument=_bound(),
        envelope=env,
        master_v2_decision="enter_long",
        account_identity="acct-1",
        environment="PRODUCTIVE_READ_ONLY",
        origin_main_sha="38d607a43aa38683cb21158aa96703866fb0a2ac",
        instrument_metadata=_META,
        pre_external_reached=True,
        terminal_disposition="PRE_EXTERNAL_EFFECT",
    )
    assert binding.envelope_digest == env.envelope_digest
    assert binding.venue_plan_digest == d1
    assert binding.final_quantity == env.quantity


def test_instrument_and_quantity_preserved_at_guard() -> None:
    env = _envelope(side="sell")
    meta = FullCoreCapitalGuardInstrumentMetadataV1(ct_val="0.1", min_sz="1", lot_sz="1")
    binding = build_full_core_capital_guard_join_binding_v1(
        canonical_decision_id="dec-short",
        bound_instrument=_bound(),
        envelope=env,
        master_v2_decision="enter_short",
        account_identity="acct-1",
        environment="OFFLINE_STUB",
        origin_main_sha="38d607a43aa38683cb21158aa96703866fb0a2ac",
        instrument_metadata=meta,
        pre_external_reached=True,
        terminal_disposition="PRE_EXTERNAL_EFFECT",
    )
    assert binding.selected_direction == "ENTER_SHORT"
    assert binding.order_side == "sell"
    assert binding.final_quantity == "2"
