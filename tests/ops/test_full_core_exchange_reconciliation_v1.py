"""Offline proofs for FULL_CORE_EXCHANGE_RECONCILIATION_V1 (40+ scenarios)."""

from __future__ import annotations

import multiprocessing as mp
import tempfile
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
    FullCoreAuthorizationBindingV1,
    STATE_HALTED_UNRESOLVED,
    STATE_RECONCILIATION_PENDING,
    STATE_RESERVED_PRE_POST,
    STATE_SUBMIT_MAY_HAVE_OCCURRED,
    STATE_TERMINAL_RECONCILED,
    full_core_atomic_mark_submit_boundary_v1,
    full_core_atomic_reserve_owner_go_authorization_v1,
    load_full_core_atomic_authorization_state_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_integration_v1 import (
    NETWORK_REQUEST_COUNT,
    POST_COUNT,
    PRIVATE_GET_COUNT,
    PRODUCTION_PROVIDER_WIRING,
    identity_from_full_core_binding_v1,
    run_full_core_offline_exchange_reconciliation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
    OfflineExchangeFixtureV1,
    build_offline_exchange_reconciliation_snapshot_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    OUTCOME_CONFIRMED_CANCELED,
    OUTCOME_CONFIRMED_FILLED,
    OUTCOME_CONFIRMED_OPEN,
    OUTCOME_CONFIRMED_PARTIALLY_FILLED,
    OUTCOME_CONFIRMED_REJECTED,
    OUTCOME_HALTED_UNRESOLVED,
    EvidenceLayer,
    ExchangeEvidenceItemV1,
    FullCoreExchangeReconciliationIdentityV1,
    FullCoreExchangeReconciliationSnapshotV1,
    LocalSubmitOutcome,
    REASON_CONFLICTING_ORDID,
    REASON_DUPLICATE_FILL_CONFLICT,
    REASON_ENV_MISMATCH,
    REASON_FILL_EXCEEDS_ORDER,
    REASON_INSTRUMENT_MISMATCH,
    REASON_NEGATIVE_REMAINING,
    REASON_ORDER_FILL_CONTRADICTION,
    REASON_ORDER_NOT_FOUND_NOT_PROOF,
    REASON_STALE_EVIDENCE,
    REASON_UNSUPPORTED_UNITS,
    REASON_WRONG_CLORDID,
    adjudicate_full_core_exchange_reconciliation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_core_exchange_reconciliation_observability_v1 import (
    STAGE_DURABLE_RECOVERY_STATE,
    STAGE_RECONCILIATION_DECISION,
    STAGE_RECONCILIATION_SNAPSHOT,
    STAGE_SUBMIT_OUTCOME,
)

CL = "ptrecontest000001"
INST = "0G-USDT-SWAP"


def _binding() -> FullCoreAuthorizationBindingV1:
    return FullCoreAuthorizationBindingV1(
        owner_go="OWNER_GO_CURRENT_FULL_CORE_PRE_POST_CAPITAL_GUARD_JOIN_V1",
        origin_main_sha="abc123",
        account_scope="acct-shadow-1",
        environment="SHADOW",
        execution_mode="OFFLINE_STUB",
        canonical_decision_id="dec-1",
        instrument_id=INST,
        native_id=INST,
        selected_direction="ENTER_LONG",
        order_side="buy",
        final_quantity="10",
        order_type="limit",
        order_price="1.0",
        venue_plan_digest="vp-digest",
        envelope_digest="env-digest",
        guard_config_digest="gc-digest",
        session_id="sess-recon-1",
        clordid=CL,
    )


def _identity(b: FullCoreAuthorizationBindingV1 | None = None):
    binding = b or _binding()
    return identity_from_full_core_binding_v1(
        binding,
        decision_outcome="ENTER",
        venue_plan_identity="vp-1",
        envelope_identity="env-1",
        submit_attempt_id="submit-1",
        local_durable_state_version="v1",
    )


def _identity_with(**overrides: object) -> FullCoreExchangeReconciliationIdentityV1:
    base = _identity()
    data = base.to_dict()
    data.update(overrides)
    data.pop("contract_id", None)
    return FullCoreExchangeReconciliationIdentityV1(**data)


def _order_row(*, state: str, sz: str = "10", acc: str = "0", s_code: str = "0") -> dict:
    return {
        "clOrdId": CL,
        "ordId": "ord-1",
        "instId": INST,
        "state": state,
        "sz": sz,
        "accFillSz": acc,
        "sCode": s_code,
    }


@pytest.fixture
def tmp_state() -> Path:
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


class TestSafetyInvariants:
    def test_no_network_post_or_get_constants(self) -> None:
        assert POST_COUNT == 0
        assert PRIVATE_GET_COUNT == 0
        assert NETWORK_REQUEST_COUNT == 0
        assert PRODUCTION_PROVIDER_WIRING == "NOT_AUTHORIZED"


@pytest.mark.parametrize(
    "scenario_id,fixture,submit_outcome,expected_outcome",
    [
        (
            "01_open",
            OfflineExchangeFixtureV1(pending_orders={"data": [_order_row(state="live")]}),
            LocalSubmitOutcome.TRANSPORT_ACK,
            OUTCOME_CONFIRMED_OPEN,
        ),
        (
            "02_filled",
            OfflineExchangeFixtureV1(
                order_history={"data": [_order_row(state="filled", acc="10")]}
            ),
            LocalSubmitOutcome.TRANSPORT_ACK,
            OUTCOME_CONFIRMED_FILLED,
        ),
        (
            "03_partial",
            OfflineExchangeFixtureV1(
                pending_orders={"data": [_order_row(state="partially_filled", acc="4")]}
            ),
            LocalSubmitOutcome.TRANSPORT_ACK,
            OUTCOME_CONFIRMED_PARTIALLY_FILLED,
        ),
        (
            "04_cancel_no_fill",
            OfflineExchangeFixtureV1(
                order_history={"data": [_order_row(state="canceled", acc="0")]}
            ),
            LocalSubmitOutcome.TRANSPORT_ACK,
            OUTCOME_CONFIRMED_CANCELED,
        ),
        (
            "05_cancel_after_partial",
            OfflineExchangeFixtureV1(
                order_history={"data": [_order_row(state="canceled", acc="3")]}
            ),
            LocalSubmitOutcome.TRANSPORT_ACK,
            OUTCOME_CONFIRMED_PARTIALLY_FILLED,
        ),
        (
            "06_rejected",
            OfflineExchangeFixtureV1(
                order_history={"data": [_order_row(state="rejected", s_code="51008")]}
            ),
            LocalSubmitOutcome.TRANSPORT_ACK,
            OUTCOME_CONFIRMED_REJECTED,
        ),
        (
            "07_timeout",
            OfflineExchangeFixtureV1(),
            LocalSubmitOutcome.TRANSPORT_TIMEOUT,
            OUTCOME_HALTED_UNRESOLVED,
        ),
        (
            "08_reset_after_send",
            OfflineExchangeFixtureV1(transport_failures=("CONNECTION_RESET",)),
            LocalSubmitOutcome.TRANSPORT_UNKNOWN,
            OUTCOME_HALTED_UNRESOLVED,
        ),
        (
            "13_not_found",
            OfflineExchangeFixtureV1(),
            LocalSubmitOutcome.TRANSPORT_ACK,
            OUTCOME_HALTED_UNRESOLVED,
        ),
        (
            "14_history_unavail",
            OfflineExchangeFixtureV1(history_unavailable=True),
            LocalSubmitOutcome.TRANSPORT_ACK,
            OUTCOME_HALTED_UNRESOLVED,
        ),
        (
            "15_incomplete_open",
            OfflineExchangeFixtureV1(
                incomplete_pagination=True, pending_orders={"data": [_order_row(state="live")]}
            ),
            LocalSubmitOutcome.TRANSPORT_ACK,
            OUTCOME_HALTED_UNRESOLVED,
        ),
        (
            "26_stale",
            OfflineExchangeFixtureV1(snapshot_freshness_proven=False),
            LocalSubmitOutcome.TRANSPORT_ACK,
            OUTCOME_HALTED_UNRESOLVED,
        ),
        (
            "29_api_error",
            OfflineExchangeFixtureV1(api_errors=("500",)),
            LocalSubmitOutcome.TRANSPORT_ACK,
            OUTCOME_HALTED_UNRESOLVED,
        ),
        (
            "30_rate_limit",
            OfflineExchangeFixtureV1(api_errors=("rate limit",)),
            LocalSubmitOutcome.TRANSPORT_ACK,
            OUTCOME_HALTED_UNRESOLVED,
        ),
        (
            "10_transport_reject",
            OfflineExchangeFixtureV1(),
            LocalSubmitOutcome.TRANSPORT_REJECT,
            OUTCOME_HALTED_UNRESOLVED,
        ),
        (
            "16_item_stale",
            OfflineExchangeFixtureV1(
                item_freshness_proven=False,
                pending_orders={"data": [_order_row(state="live")]},
            ),
            LocalSubmitOutcome.TRANSPORT_ACK,
            OUTCOME_HALTED_UNRESOLVED,
        ),
        (
            "25_positions_only_no_order",
            OfflineExchangeFixtureV1(
                positions={"data": [{"instId": INST, "pos": "1", "avgPx": "1.0"}]}
            ),
            LocalSubmitOutcome.TRANSPORT_ACK,
            OUTCOME_HALTED_UNRESOLVED,
        ),
        (
            "28_transport_fail_no_evidence",
            OfflineExchangeFixtureV1(transport_failures=("TIMEOUT",)),
            LocalSubmitOutcome.TRANSPORT_ACK,
            OUTCOME_HALTED_UNRESOLVED,
        ),
        (
            "32_unknown_order_state",
            OfflineExchangeFixtureV1(
                pending_orders={"data": [_order_row(state="expired_unknown")]}
            ),
            LocalSubmitOutcome.TRANSPORT_ACK,
            OUTCOME_HALTED_UNRESOLVED,
        ),
    ],
)
def test_core_scenarios(
    scenario_id: str,
    fixture: OfflineExchangeFixtureV1,
    submit_outcome: LocalSubmitOutcome,
    expected_outcome: str,
) -> None:
    ident = _identity()
    res = run_full_core_offline_exchange_reconciliation_v1(
        identity=ident,
        binding=_binding(),
        fixture=fixture,
        local_submit_outcome=submit_outcome,
    )
    assert res.decision.outcome == expected_outcome, scenario_id


def test_09_crash_before_submit_never_submitted() -> None:
    ident = _identity()
    res = run_full_core_offline_exchange_reconciliation_v1(
        identity=ident,
        binding=_binding(),
        fixture=OfflineExchangeFixtureV1(),
        local_submit_outcome=LocalSubmitOutcome.NOT_SUBMITTED,
        proven_never_submitted=True,
    )
    assert res.decision.outcome == OUTCOME_CONFIRMED_CANCELED


def test_19_fill_exceeds_order() -> None:
    ident = _identity()
    fixture = OfflineExchangeFixtureV1(
        order_history={"data": [_order_row(state="partially_filled", sz="10", acc="10")]},
        fills={
            "data": [
                {"clOrdId": CL, "fillSz": "6", "fillId": "f1"},
                {"clOrdId": CL, "fillSz": "6", "fillId": "f2"},
            ]
        },
    )
    res = run_full_core_offline_exchange_reconciliation_v1(
        identity=ident,
        binding=_binding(),
        fixture=fixture,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    assert res.decision.outcome == OUTCOME_HALTED_UNRESOLVED
    assert REASON_FILL_EXCEEDS_ORDER in res.decision.reasons


def test_11_identity_digest_mismatch() -> None:
    ident = _identity()
    snap = build_offline_exchange_reconciliation_snapshot_v1(
        identity=ident,
        fixture=OfflineExchangeFixtureV1(pending_orders={"data": [_order_row(state="live")]}),
    )
    tampered = FullCoreExchangeReconciliationSnapshotV1(
        provider=snap.provider,
        simulation_mode=snap.simulation_mode,
        identity_digest="deadbeef",
        evidence_items=snap.evidence_items,
        incomplete_pagination=False,
        history_unavailable=False,
        snapshot_freshness_proven=True,
        transport_failures=(),
        api_errors=(),
    )
    dec = adjudicate_full_core_exchange_reconciliation_v1(
        identity=ident,
        snapshot=tampered,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    assert dec.outcome == OUTCOME_HALTED_UNRESOLVED
    assert "IDENTITY_DIGEST_MISMATCH" in dec.reasons


def test_17_wrong_environment() -> None:
    ident = _identity()
    snap = build_offline_exchange_reconciliation_snapshot_v1(
        identity=ident,
        fixture=OfflineExchangeFixtureV1(pending_orders={"data": [_order_row(state="live")]}),
    )
    item = snap.evidence_items[0]
    bad = ExchangeEvidenceItemV1(
        layer=item.layer,
        source=item.source,
        account=item.account,
        environment="LIVE",
        instrument=item.instrument,
        observed_at=item.observed_at,
        received_at=item.received_at,
        freshness_proven=True,
        query_scope=item.query_scope,
        response_status=item.response_status,
        raw_reference=item.raw_reference,
        canonical_identity_digest=item.canonical_identity_digest,
        payload=item.payload,
    )
    tampered = FullCoreExchangeReconciliationSnapshotV1(
        provider=snap.provider,
        simulation_mode=snap.simulation_mode,
        identity_digest=snap.identity_digest,
        evidence_items=(bad,),
        incomplete_pagination=False,
        history_unavailable=False,
        snapshot_freshness_proven=True,
        transport_failures=(),
        api_errors=(),
    )
    dec = adjudicate_full_core_exchange_reconciliation_v1(
        identity=ident,
        snapshot=tampered,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    assert dec.outcome == OUTCOME_HALTED_UNRESOLVED
    assert REASON_ENV_MISMATCH in dec.reasons


def test_18_wrong_instrument() -> None:
    ident = _identity()
    snap = build_offline_exchange_reconciliation_snapshot_v1(
        identity=ident,
        fixture=OfflineExchangeFixtureV1(pending_orders={"data": [_order_row(state="live")]}),
    )
    item = snap.evidence_items[0]
    bad = ExchangeEvidenceItemV1(
        layer=item.layer,
        source=item.source,
        account=item.account,
        environment=item.environment,
        instrument="BTC-USDT-SWAP",
        observed_at=item.observed_at,
        received_at=item.received_at,
        freshness_proven=True,
        query_scope=item.query_scope,
        response_status=item.response_status,
        raw_reference=item.raw_reference,
        canonical_identity_digest=item.canonical_identity_digest,
        payload=item.payload,
    )
    tampered = FullCoreExchangeReconciliationSnapshotV1(
        provider=snap.provider,
        simulation_mode=snap.simulation_mode,
        identity_digest=snap.identity_digest,
        evidence_items=(bad,),
        incomplete_pagination=False,
        history_unavailable=False,
        snapshot_freshness_proven=True,
        transport_failures=(),
        api_errors=(),
    )
    dec = adjudicate_full_core_exchange_reconciliation_v1(
        identity=ident,
        snapshot=tampered,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    assert dec.outcome == OUTCOME_HALTED_UNRESOLVED
    assert REASON_INSTRUMENT_MISMATCH in dec.reasons


def test_20_duplicate_fill_id_conflict() -> None:
    ident = _identity()
    fixture = OfflineExchangeFixtureV1(
        order_history={"data": [_order_row(state="partially_filled", sz="10", acc="4")]},
        fills={
            "data": [
                {"clOrdId": CL, "fillSz": "2", "fillId": "f-dup"},
                {"clOrdId": CL, "fillSz": "3", "fillId": "f-dup"},
            ]
        },
    )
    res = run_full_core_offline_exchange_reconciliation_v1(
        identity=ident,
        binding=_binding(),
        fixture=fixture,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    assert res.decision.outcome == OUTCOME_HALTED_UNRESOLVED
    assert REASON_DUPLICATE_FILL_CONFLICT in res.decision.reasons


def test_22_conflicting_ordid() -> None:
    ident = _identity_with(exchange_ord_id="ord-bound")
    snap = build_offline_exchange_reconciliation_snapshot_v1(
        identity=ident,
        fixture=OfflineExchangeFixtureV1(
            pending_orders={
                "data": [
                    {
                        **_order_row(state="live"),
                        "ordId": "ord-other",
                    }
                ]
            }
        ),
    )
    dec = adjudicate_full_core_exchange_reconciliation_v1(
        identity=ident,
        snapshot=snap,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    assert dec.outcome == OUTCOME_HALTED_UNRESOLVED
    assert REASON_CONFLICTING_ORDID in dec.reasons


def test_24_negative_remaining_qty() -> None:
    ident = _identity()
    fixture = OfflineExchangeFixtureV1(
        order_history={"data": [_order_row(state="partially_filled", sz="10", acc="12")]},
        fills={"data": [{"clOrdId": CL, "fillSz": "12", "fillId": "f1"}]},
    )
    res = run_full_core_offline_exchange_reconciliation_v1(
        identity=ident,
        binding=_binding(),
        fixture=fixture,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    assert res.decision.outcome == OUTCOME_HALTED_UNRESOLVED
    assert REASON_NEGATIVE_REMAINING in res.decision.reasons


def test_27_unsupported_quantity_unit() -> None:
    ident = _identity_with(quantity_unit="USDT")
    snap = build_offline_exchange_reconciliation_snapshot_v1(
        identity=ident,
        fixture=OfflineExchangeFixtureV1(pending_orders={"data": [_order_row(state="live")]}),
    )
    dec = adjudicate_full_core_exchange_reconciliation_v1(
        identity=ident,
        snapshot=snap,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    assert dec.outcome == OUTCOME_HALTED_UNRESOLVED
    assert REASON_UNSUPPORTED_UNITS in dec.reasons


def test_31_order_fill_contradiction() -> None:
    ident = _identity()
    fixture = OfflineExchangeFixtureV1(
        order_history={"data": [_order_row(state="partially_filled", sz="10", acc="6")]},
        fills={
            "data": [
                {"clOrdId": CL, "fillSz": "2", "fillId": "f1"},
                {"clOrdId": CL, "fillSz": "2", "fillId": "f2"},
            ]
        },
    )
    res = run_full_core_offline_exchange_reconciliation_v1(
        identity=ident,
        binding=_binding(),
        fixture=fixture,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    assert res.decision.outcome == OUTCOME_HALTED_UNRESOLVED
    assert REASON_ORDER_FILL_CONTRADICTION in res.decision.reasons


def test_21_wrong_clordid_evidence() -> None:
    ident = _identity()
    snap = build_offline_exchange_reconciliation_snapshot_v1(
        identity=ident,
        fixture=OfflineExchangeFixtureV1(pending_orders={"data": [_order_row(state="live")]}),
    )
    bad_item = ExchangeEvidenceItemV1(
        layer=EvidenceLayer.EXCHANGE_ORDER_STATE,
        source="tamper",
        account=ident.account_identity,
        environment=ident.execution_environment,
        instrument=ident.instrument_id,
        observed_at="0",
        received_at="t",
        freshness_proven=True,
        query_scope="x",
        response_status="200",
        raw_reference="x",
        canonical_identity_digest=ident.identity_digest(),
        payload={"clOrdId": "wrong-id", "state": "live", "instId": INST},
    )
    tampered = FullCoreExchangeReconciliationSnapshotV1(
        provider=snap.provider,
        simulation_mode=snap.simulation_mode,
        identity_digest=snap.identity_digest,
        evidence_items=snap.evidence_items + (bad_item,),
        incomplete_pagination=False,
        history_unavailable=False,
        snapshot_freshness_proven=True,
        transport_failures=(),
        api_errors=(),
    )
    dec = adjudicate_full_core_exchange_reconciliation_v1(
        identity=ident,
        snapshot=tampered,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    assert dec.outcome == OUTCOME_HALTED_UNRESOLVED
    assert REASON_WRONG_CLORDID in dec.reasons


def test_23_wrong_account() -> None:
    ident = _identity()
    snap = build_offline_exchange_reconciliation_snapshot_v1(
        identity=ident,
        fixture=OfflineExchangeFixtureV1(pending_orders={"data": [_order_row(state="live")]}),
    )
    item = snap.evidence_items[0]
    bad = ExchangeEvidenceItemV1(
        layer=item.layer,
        source=item.source,
        account="other-account",
        environment=item.environment,
        instrument=item.instrument,
        observed_at=item.observed_at,
        received_at=item.received_at,
        freshness_proven=True,
        query_scope=item.query_scope,
        response_status=item.response_status,
        raw_reference=item.raw_reference,
        canonical_identity_digest=item.canonical_identity_digest,
        payload=item.payload,
    )
    tampered = FullCoreExchangeReconciliationSnapshotV1(
        provider=snap.provider,
        simulation_mode=snap.simulation_mode,
        identity_digest=snap.identity_digest,
        evidence_items=(bad,),
        incomplete_pagination=False,
        history_unavailable=False,
        snapshot_freshness_proven=True,
        transport_failures=(),
        api_errors=(),
    )
    dec = adjudicate_full_core_exchange_reconciliation_v1(
        identity=ident,
        snapshot=tampered,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    assert dec.outcome == OUTCOME_HALTED_UNRESOLVED


def test_33_idempotent_reconciliation() -> None:
    ident = _identity()
    fixture = OfflineExchangeFixtureV1(
        order_history={"data": [_order_row(state="filled", acc="10")]}
    )
    a = run_full_core_offline_exchange_reconciliation_v1(
        identity=ident,
        binding=_binding(),
        fixture=fixture,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    b = run_full_core_offline_exchange_reconciliation_v1(
        identity=ident,
        binding=_binding(),
        fixture=fixture,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    assert a.decision.outcome == b.decision.outcome == OUTCOME_CONFIRMED_FILLED


def test_35_owner_go_remains_consumed_after_terminal(tmp_state: Path) -> None:
    binding = _binding()
    ident = _identity(binding)
    full_core_atomic_reserve_owner_go_authorization_v1(state_dir=tmp_state, binding=binding)
    full_core_atomic_mark_submit_boundary_v1(state_dir=tmp_state, binding=binding)
    run_full_core_offline_exchange_reconciliation_v1(
        identity=ident,
        binding=binding,
        fixture=OfflineExchangeFixtureV1(
            order_history={"data": [_order_row(state="filled", acc="10")]}
        ),
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
        state_dir=tmp_state,
        apply_durable_state=True,
    )
    st = load_full_core_atomic_authorization_state_v1(
        state_dir=tmp_state, consumption_key=binding.consumption_key()
    )
    assert st is not None
    assert st.state == STATE_TERMINAL_RECONCILED
    assert st.authorization_permanently_consumed is True


def test_36_no_automatic_entry_retry(tmp_state: Path) -> None:
    binding = _binding()
    ident = _identity(binding)
    full_core_atomic_reserve_owner_go_authorization_v1(state_dir=tmp_state, binding=binding)
    res = run_full_core_offline_exchange_reconciliation_v1(
        identity=ident,
        binding=binding,
        fixture=OfflineExchangeFixtureV1(),
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_TIMEOUT,
        state_dir=tmp_state,
        apply_durable_state=True,
    )
    assert res.decision.outcome == OUTCOME_HALTED_UNRESOLVED
    assert res.post_count == 0
    st = load_full_core_atomic_authorization_state_v1(
        state_dir=tmp_state, consumption_key=binding.consumption_key()
    )
    assert st is not None
    assert st.state == STATE_HALTED_UNRESOLVED


def test_12_restart_unknown_preserved(tmp_state: Path) -> None:
    binding = _binding()
    ident = _identity(binding)
    full_core_atomic_reserve_owner_go_authorization_v1(state_dir=tmp_state, binding=binding)
    full_core_atomic_mark_submit_boundary_v1(state_dir=tmp_state, binding=binding)
    run_full_core_offline_exchange_reconciliation_v1(
        identity=ident,
        binding=binding,
        fixture=OfflineExchangeFixtureV1(),
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_UNKNOWN,
        state_dir=tmp_state,
        apply_durable_state=True,
    )
    st = load_full_core_atomic_authorization_state_v1(
        state_dir=tmp_state, consumption_key=binding.consumption_key()
    )
    assert st is not None
    assert st.state == STATE_HALTED_UNRESOLVED


def test_38_ghv_forward_join_all_stages(tmp_state: Path) -> None:
    binding = _binding()
    ident = _identity(binding)
    full_core_atomic_reserve_owner_go_authorization_v1(state_dir=tmp_state, binding=binding)
    full_core_atomic_mark_submit_boundary_v1(state_dir=tmp_state, binding=binding)
    res = run_full_core_offline_exchange_reconciliation_v1(
        identity=ident,
        binding=binding,
        fixture=OfflineExchangeFixtureV1(pending_orders={"data": [_order_row(state="live")]}),
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
        state_dir=tmp_state,
        apply_durable_state=True,
    )
    stages = [r["stage"] for r in res.ghv_bundle["ghv_full_core_exchange_reconciliation_stages"]]
    assert stages == [
        STAGE_SUBMIT_OUTCOME,
        STAGE_RECONCILIATION_SNAPSHOT,
        STAGE_RECONCILIATION_DECISION,
        STAGE_DURABLE_RECOVERY_STATE,
    ]
    assert all(
        r.get("ghv_authority") == "NONE"
        for r in res.ghv_bundle["ghv_full_core_exchange_reconciliation_stages"]
    )


def test_39_stale_evidence_reason_on_item() -> None:
    ident = _identity()
    res = run_full_core_offline_exchange_reconciliation_v1(
        identity=ident,
        binding=_binding(),
        fixture=OfflineExchangeFixtureV1(
            item_freshness_proven=False,
            pending_orders={"data": [_order_row(state="live")]},
        ),
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    assert res.decision.outcome == OUTCOME_HALTED_UNRESOLVED
    assert REASON_STALE_EVIDENCE in res.decision.reasons


def test_40_decimal_partial_remaining_consistent() -> None:
    ident = _identity()
    res = run_full_core_offline_exchange_reconciliation_v1(
        identity=ident,
        binding=_binding(),
        fixture=OfflineExchangeFixtureV1(
            pending_orders={"data": [_order_row(state="partially_filled", sz="10", acc="4")]}
        ),
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    assert res.decision.outcome == OUTCOME_CONFIRMED_PARTIALLY_FILLED
    assert res.decision.remaining_qty == "6"
    assert res.decision.cumulative_filled_qty == "4"


def test_13_not_found_reason() -> None:
    dec = adjudicate_full_core_exchange_reconciliation_v1(
        identity=_identity(),
        snapshot=build_offline_exchange_reconciliation_snapshot_v1(
            identity=_identity(), fixture=OfflineExchangeFixtureV1()
        ),
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    assert REASON_ORDER_NOT_FOUND_NOT_PROOF in dec.reasons


def test_37_partial_open_atomic_pending(tmp_state: Path) -> None:
    binding = _binding()
    ident = _identity(binding)
    full_core_atomic_reserve_owner_go_authorization_v1(state_dir=tmp_state, binding=binding)
    full_core_atomic_mark_submit_boundary_v1(state_dir=tmp_state, binding=binding)
    res = run_full_core_offline_exchange_reconciliation_v1(
        identity=ident,
        binding=binding,
        fixture=OfflineExchangeFixtureV1(pending_orders={"data": [_order_row(state="live")]}),
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
        state_dir=tmp_state,
        apply_durable_state=True,
    )
    assert res.decision.outcome == OUTCOME_CONFIRMED_OPEN
    st = load_full_core_atomic_authorization_state_v1(
        state_dir=tmp_state, consumption_key=binding.consumption_key()
    )
    assert st is not None
    assert st.state == STATE_RECONCILIATION_PENDING


def _reserve_in_child(state_dir: str, key: str) -> None:
    binding = _binding()
    full_core_atomic_reserve_owner_go_authorization_v1(state_dir=Path(state_dir), binding=binding)
    assert binding.consumption_key() == key


def test_34_concurrent_reservation_fail_closed(tmp_path: Path) -> None:
    binding = _binding()
    key = binding.consumption_key()
    p = mp.Process(target=_reserve_in_child, args=(str(tmp_path), key))
    p.start()
    p.join(timeout=10)
    assert p.exitcode == 0
    with pytest.raises(Exception):
        full_core_atomic_reserve_owner_go_authorization_v1(state_dir=tmp_path, binding=binding)
