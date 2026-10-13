"""OKX read-only reconciliation adapter (injected transport; no network)."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest

from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
    FreshPretradeGetTransportResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
    STATE_RECONCILIATION_PENDING,
    STATE_TERMINAL_RECONCILED,
    full_core_atomic_mark_submit_boundary_v1,
    full_core_atomic_reserve_owner_go_authorization_v1,
    load_full_core_atomic_authorization_state_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_integration_v1 import (
    POST_COUNT,
    PRIVATE_GET_COUNT,
    PRODUCTION_PROVIDER_WIRING,
    identity_from_full_core_binding_v1,
    run_full_core_offline_exchange_reconciliation_v1,
    run_full_core_okx_injected_exchange_reconciliation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
    OfflineExchangeFixtureV1,
    build_offline_exchange_reconciliation_snapshot_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_okx_read_only_provider_v1 import (
    PRODUCTION_PROVIDER_WIRING as OKX_PROVIDER_WIRING,
    fetch_okx_read_only_reconciliation_snapshot_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    OUTCOME_CONFIRMED_FILLED,
    OUTCOME_CONFIRMED_OPEN,
    OUTCOME_HALTED_UNRESOLVED,
    RECONCILIATION_PROVIDER_OKX_EEA_READ_ONLY_GET,
    LocalSubmitOutcome,
    REASON_CONFLICTING_ORDID,
    REASON_CONFLICTING_ORDER_STATE,
    REASON_FRESHNESS_UNPROVEN,
    REASON_INCOMPLETE_PAGINATION,
    REASON_INSTRUMENT_MISMATCH,
    REASON_ORDER_NOT_FOUND_NOT_PROOF,
    REASON_STALE_EVIDENCE,
    REASON_WRONG_CLORDID,
    EvidenceLayer,
    adjudicate_full_core_exchange_reconciliation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_core_exchange_reconciliation_observability_v1 import (
    STAGE_DURABLE_RECOVERY_STATE,
    STAGE_RECONCILIATION_DECISION,
    STAGE_RECONCILIATION_SNAPSHOT,
    STAGE_SUBMIT_OUTCOME,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    READ_ONLY_EXACT_ORDER_LOOKUP_PATH,
)
from tests.ops.test_full_core_exchange_reconciliation_v1 import (
    CL,
    INST,
    _binding,
    _identity,
    _order_row,
)

ENDPOINT_ORDERS_PENDING = "/api/v5/trade/orders-pending"
ENDPOINT_ORDERS_HISTORY = "/api/v5/trade/orders-history"
ENDPOINT_TRADE_FILLS = "/api/v5/trade/fills"
ENDPOINT_ACCOUNT_POSITIONS = "/api/v5/account/positions"


def _ok_payload(data: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"code": "0", "data": list(data or [])}


def _result(payload: dict[str, Any], *, fresh: bool = True) -> FreshPretradeGetTransportResultV1:
    return FreshPretradeGetTransportResultV1(
        get_performed=True,
        method="GET",
        endpoint="",
        http_status=200,
        payload=payload,
        auth_header_sent=True,
        transport_class=TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
        venue_live_contact=False,
        historical_reuse=not fresh,
        error_class="",
    )


class FixtureBackedOkxReadOnlyTransport:
    """Maps OfflineExchangeFixtureV1 buckets onto OKX GET endpoints (test double only)."""

    def __init__(self, fixture: OfflineExchangeFixtureV1) -> None:
        self.fixture = fixture
        self.request_count = 0

    def get(
        self,
        *,
        endpoint: str,
        auth_required: bool,
        pretrade_decision_id: str,
        get_cache_policy: str = GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    ) -> FreshPretradeGetTransportResultV1:
        del auth_required, pretrade_decision_id, get_cache_policy
        self.request_count += 1
        parsed = urlparse(endpoint if "://" in endpoint else f"https://eea.okx.com{endpoint}")
        path = parsed.path

        if self.fixture.transport_failures:
            return FreshPretradeGetTransportResultV1(
                get_performed=False,
                method="GET",
                endpoint=endpoint,
                http_status=0,
                payload=None,
                auth_header_sent=True,
                transport_class=TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
                venue_live_contact=False,
                historical_reuse=False,
                error_class="TIMEOUT",
            )

        fresh = self.fixture.item_freshness_proven and self.fixture.snapshot_freshness_proven
        status = self.fixture.response_status

        if path == ENDPOINT_ORDERS_PENDING:
            payload = self.fixture.pending_orders or _ok_payload([])
        elif path == ENDPOINT_ORDERS_HISTORY:
            payload = self.fixture.order_history or _ok_payload([])
        elif path == ENDPOINT_TRADE_FILLS:
            payload = self.fixture.fills or _ok_payload([])
        elif path == ENDPOINT_ACCOUNT_POSITIONS:
            payload = self.fixture.positions or _ok_payload([])
        elif path == READ_ONLY_EXACT_ORDER_LOOKUP_PATH:
            qs = parse_qs(parsed.query)
            cl = (qs.get("clOrdId") or [""])[0]
            rows: list[dict[str, Any]] = []
            for bucket in (
                self.fixture.pending_orders,
                self.fixture.order_history,
            ):
                if isinstance(bucket, dict):
                    for row in bucket.get("data") or []:
                        if isinstance(row, dict) and str(row.get("clOrdId") or "") == cl:
                            rows.append(dict(row))
            payload = _ok_payload(rows)
        else:
            payload = _ok_payload([])

        if self.fixture.api_errors and path == ENDPOINT_ORDERS_HISTORY:
            payload = {"code": "50011", "msg": "rate limit", "data": []}

        if status != "200" and status.isdigit():
            return FreshPretradeGetTransportResultV1(
                get_performed=False,
                method="GET",
                endpoint=endpoint,
                http_status=int(status),
                payload=payload if isinstance(payload, dict) else None,
                auth_header_sent=True,
                transport_class=TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
                venue_live_contact=False,
                historical_reuse=False,
                error_class="HTTP_ERROR",
            )

        return _result(payload if isinstance(payload, dict) else _ok_payload(), fresh=fresh)


@pytest.fixture
def tmp_state() -> Path:
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


class TestModuleSafety:
    def test_standing_wiring_constants(self) -> None:
        assert POST_COUNT == 0
        assert PRIVATE_GET_COUNT == 0
        assert PRODUCTION_PROVIDER_WIRING == "NOT_AUTHORIZED"
        assert OKX_PROVIDER_WIRING == "NOT_AUTHORIZED"


@pytest.mark.parametrize(
    "fixture,submit_outcome,expected",
    [
        (
            OfflineExchangeFixtureV1(pending_orders={"data": [_order_row(state="live")]}),
            LocalSubmitOutcome.TRANSPORT_ACK,
            OUTCOME_CONFIRMED_OPEN,
        ),
        (
            OfflineExchangeFixtureV1(
                order_history={"data": [_order_row(state="filled", acc="10")]}
            ),
            LocalSubmitOutcome.TRANSPORT_ACK,
            OUTCOME_CONFIRMED_FILLED,
        ),
    ],
)
def test_okx_adapter_matches_offline_adjudication(
    fixture: OfflineExchangeFixtureV1,
    submit_outcome: LocalSubmitOutcome,
    expected: str,
) -> None:
    ident = _identity()
    offline_snap = build_offline_exchange_reconciliation_snapshot_v1(
        identity=ident, fixture=fixture
    )
    offline_dec = adjudicate_full_core_exchange_reconciliation_v1(
        identity=ident,
        snapshot=offline_snap,
        local_submit_outcome=submit_outcome,
    )
    transport = FixtureBackedOkxReadOnlyTransport(fixture)
    okx_snap = fetch_okx_read_only_reconciliation_snapshot_v1(
        identity=ident,
        read_only_get_transport=transport,
        pretrade_decision_id="pretrade-test-1",
    )
    okx_dec = adjudicate_full_core_exchange_reconciliation_v1(
        identity=ident,
        snapshot=okx_snap,
        local_submit_outcome=submit_outcome,
    )
    assert offline_dec.outcome == expected
    assert okx_dec.outcome == expected
    assert okx_snap.provider == RECONCILIATION_PROVIDER_OKX_EEA_READ_ONLY_GET


def test_ghv_forward_join_okx_injected_path(tmp_state: Path) -> None:
    binding = _binding()
    ident = _identity(binding)
    fixture = OfflineExchangeFixtureV1(pending_orders={"data": [_order_row(state="live")]})
    full_core_atomic_reserve_owner_go_authorization_v1(state_dir=tmp_state, binding=binding)
    full_core_atomic_mark_submit_boundary_v1(state_dir=tmp_state, binding=binding)
    transport = FixtureBackedOkxReadOnlyTransport(fixture)
    res = run_full_core_okx_injected_exchange_reconciliation_v1(
        identity=ident,
        binding=binding,
        read_only_get_transport=transport,
        pretrade_decision_id="pretrade-ghv-fwd",
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
    assert res.provider == RECONCILIATION_PROVIDER_OKX_EEA_READ_ONLY_GET
    st = load_full_core_atomic_authorization_state_v1(
        state_dir=tmp_state, consumption_key=binding.consumption_key()
    )
    assert st is not None
    assert st.state == STATE_RECONCILIATION_PENDING


def test_ghv_reverse_join_offline_and_okx_runs_align() -> None:
    """Reverse join: offline stub run ↔ OKX injected run share decision + terminal semantics."""
    binding = _binding()
    ident = _identity(binding)
    fixture = OfflineExchangeFixtureV1(
        order_history={"data": [_order_row(state="filled", acc="10")]}
    )
    offline_run = run_full_core_offline_exchange_reconciliation_v1(
        identity=ident,
        binding=binding,
        fixture=fixture,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    okx_run = run_full_core_okx_injected_exchange_reconciliation_v1(
        identity=ident,
        binding=binding,
        read_only_get_transport=FixtureBackedOkxReadOnlyTransport(fixture),
        pretrade_decision_id="pretrade-ghv-rev",
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    assert offline_run.decision.outcome == okx_run.decision.outcome == OUTCOME_CONFIRMED_FILLED
    assert (
        offline_run.decision.recommended_atomic_state == okx_run.decision.recommended_atomic_state
    )
    offline_stages = [
        s["stage"] for s in offline_run.ghv_bundle["ghv_full_core_exchange_reconciliation_stages"]
    ]
    okx_stages = [
        s["stage"] for s in okx_run.ghv_bundle["ghv_full_core_exchange_reconciliation_stages"]
    ]
    assert offline_stages == okx_stages


def test_stale_item_freshness_halts() -> None:
    ident = _identity()
    fixture = OfflineExchangeFixtureV1(
        item_freshness_proven=False,
        pending_orders={"data": [_order_row(state="live")]},
    )
    snap = fetch_okx_read_only_reconciliation_snapshot_v1(
        identity=ident,
        read_only_get_transport=FixtureBackedOkxReadOnlyTransport(fixture),
        pretrade_decision_id="pretrade-stale",
    )
    dec = adjudicate_full_core_exchange_reconciliation_v1(
        identity=ident,
        snapshot=snap,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    assert dec.outcome == OUTCOME_HALTED_UNRESOLVED
    assert REASON_STALE_EVIDENCE in dec.reasons or REASON_FRESHNESS_UNPROVEN in dec.reasons


def test_incomplete_pagination_halts() -> None:
    ident = _identity()
    rows = [_order_row(state="live") for _ in range(100)]
    fixture = OfflineExchangeFixtureV1(order_history={"data": rows})
    snap = fetch_okx_read_only_reconciliation_snapshot_v1(
        identity=ident,
        read_only_get_transport=FixtureBackedOkxReadOnlyTransport(fixture),
        pretrade_decision_id="pretrade-page",
    )
    assert snap.incomplete_pagination is True
    dec = adjudicate_full_core_exchange_reconciliation_v1(
        identity=ident,
        snapshot=snap,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    assert dec.outcome == OUTCOME_HALTED_UNRESOLVED
    assert REASON_INCOMPLETE_PAGINATION in dec.reasons


def test_wrong_inst_id_row_records_conflict_not_silent() -> None:
    ident = _identity()
    row = _order_row(state="live")
    row["instId"] = "OTHER-USDT-SWAP"
    fixture = OfflineExchangeFixtureV1(pending_orders={"data": [row]})
    snap = fetch_okx_read_only_reconciliation_snapshot_v1(
        identity=ident,
        read_only_get_transport=FixtureBackedOkxReadOnlyTransport(fixture),
        pretrade_decision_id="pretrade-inst",
    )
    assert any("INSTRUMENT_IDENTITY_MISMATCH" in c for c in snap.identity_conflicts)
    assert not any(item.layer is EvidenceLayer.EXCHANGE_ORDER_STATE for item in snap.evidence_items)
    dec = adjudicate_full_core_exchange_reconciliation_v1(
        identity=ident,
        snapshot=snap,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    assert dec.outcome == OUTCOME_HALTED_UNRESOLVED
    assert REASON_INSTRUMENT_MISMATCH in dec.reasons


class TestIdentityHardeningRegression:
    def test_ord_id_mismatch_against_identity_exchange_ord_id(self) -> None:
        binding = _binding()
        ident = identity_from_full_core_binding_v1(
            binding,
            decision_outcome="ENTER",
            venue_plan_identity="vp-1",
            envelope_identity="env-1",
            submit_attempt_id="submit-1",
            local_durable_state_version="v1",
            exchange_ord_id="ord-expected",
        )
        row = _order_row(state="live")
        row["ordId"] = "ord-wrong"
        fixture = OfflineExchangeFixtureV1(pending_orders={"data": [row]})
        snap = fetch_okx_read_only_reconciliation_snapshot_v1(
            identity=ident,
            read_only_get_transport=FixtureBackedOkxReadOnlyTransport(fixture),
            pretrade_decision_id="pretrade-ord",
        )
        assert any("CONFLICTING_ORDID" in c for c in snap.identity_conflicts)
        dec = adjudicate_full_core_exchange_reconciliation_v1(
            identity=ident,
            snapshot=snap,
            local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
        )
        assert REASON_CONFLICTING_ORDID in dec.reasons

    def test_conflicting_ord_ids_same_cl_in_one_surface(self) -> None:
        ident = _identity()
        r1 = _order_row(state="live")
        r1["ordId"] = "ord-a"
        r2 = _order_row(state="live")
        r2["ordId"] = "ord-b"
        fixture = OfflineExchangeFixtureV1(pending_orders={"data": [r1, r2]})
        snap = fetch_okx_read_only_reconciliation_snapshot_v1(
            identity=ident,
            read_only_get_transport=FixtureBackedOkxReadOnlyTransport(fixture),
            pretrade_decision_id="pretrade-multi-ord",
        )
        assert any("CONFLICTING_ORDID" in c for c in snap.identity_conflicts)
        dec = adjudicate_full_core_exchange_reconciliation_v1(
            identity=ident,
            snapshot=snap,
            local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
        )
        assert REASON_CONFLICTING_ORDID in dec.reasons

    def test_duplicate_identical_order_rows_remain_open(self) -> None:
        ident = _identity()
        row = _order_row(state="live")
        fixture = OfflineExchangeFixtureV1(
            pending_orders={"data": [dict(row)]},
            order_history={"data": [dict(row)]},
        )
        res = run_full_core_okx_injected_exchange_reconciliation_v1(
            identity=ident,
            binding=_binding(),
            read_only_get_transport=FixtureBackedOkxReadOnlyTransport(fixture),
            pretrade_decision_id="pretrade-dup",
            local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
        )
        assert res.decision.outcome == OUTCOME_CONFIRMED_OPEN

    def test_rate_limit_on_history_halts_without_terminal(self) -> None:
        ident = _identity()
        fixture = OfflineExchangeFixtureV1(
            api_errors=("history",),
            pending_orders={"data": [_order_row(state="live")]},
        )
        snap = fetch_okx_read_only_reconciliation_snapshot_v1(
            identity=ident,
            read_only_get_transport=FixtureBackedOkxReadOnlyTransport(fixture),
            pretrade_decision_id="pretrade-rate",
        )
        dec = adjudicate_full_core_exchange_reconciliation_v1(
            identity=ident,
            snapshot=snap,
            local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
        )
        assert dec.outcome == OUTCOME_HALTED_UNRESOLVED
        assert dec.reconciliation_complete is False

    def test_transport_timeout_recorded_in_api_errors(self) -> None:
        ident = _identity()
        fixture = OfflineExchangeFixtureV1(transport_failures=("timeout",))
        snap = fetch_okx_read_only_reconciliation_snapshot_v1(
            identity=ident,
            read_only_get_transport=FixtureBackedOkxReadOnlyTransport(fixture),
            pretrade_decision_id="pretrade-timeout",
        )
        assert any("TRANSPORT_TIMEOUT" in e for e in snap.api_errors)
        dec = adjudicate_full_core_exchange_reconciliation_v1(
            identity=ident,
            snapshot=snap,
            local_submit_outcome=LocalSubmitOutcome.TRANSPORT_TIMEOUT,
        )
        assert dec.outcome == OUTCOME_HALTED_UNRESOLVED

    def test_full_page_without_matching_cl_still_incomplete_pagination(self) -> None:
        ident = _identity()
        foreign = _order_row(state="live")
        foreign["clOrdId"] = "other-client-id"
        rows = [foreign for _ in range(100)]
        fixture = OfflineExchangeFixtureV1(order_history={"data": rows})
        snap = fetch_okx_read_only_reconciliation_snapshot_v1(
            identity=ident,
            read_only_get_transport=FixtureBackedOkxReadOnlyTransport(fixture),
            pretrade_decision_id="pretrade-page-nomatch",
        )
        assert snap.incomplete_pagination is True
        dec = adjudicate_full_core_exchange_reconciliation_v1(
            identity=ident,
            snapshot=snap,
            local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
        )
        assert REASON_INCOMPLETE_PAGINATION in dec.reasons


def test_order_conflict_live_and_filled(tmp_state: Path) -> None:
    binding = _binding()
    ident = _identity(binding)
    full_core_atomic_reserve_owner_go_authorization_v1(state_dir=tmp_state, binding=binding)
    full_core_atomic_mark_submit_boundary_v1(state_dir=tmp_state, binding=binding)
    fixture = OfflineExchangeFixtureV1(
        pending_orders={"data": [_order_row(state="live", acc="0")]},
        order_history={"data": [_order_row(state="filled", acc="10")]},
    )
    res = run_full_core_okx_injected_exchange_reconciliation_v1(
        identity=ident,
        binding=binding,
        read_only_get_transport=FixtureBackedOkxReadOnlyTransport(fixture),
        pretrade_decision_id="pretrade-conflict",
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
        state_dir=tmp_state,
        apply_durable_state=True,
    )
    assert res.decision.outcome == OUTCOME_HALTED_UNRESOLVED
    assert REASON_CONFLICTING_ORDER_STATE in res.decision.reasons


def test_atomic_terminal_reconciled_filled(tmp_state: Path) -> None:
    binding = _binding()
    ident = _identity(binding)
    fixture = OfflineExchangeFixtureV1(
        order_history={"data": [_order_row(state="filled", acc="10")]}
    )
    full_core_atomic_reserve_owner_go_authorization_v1(state_dir=tmp_state, binding=binding)
    full_core_atomic_mark_submit_boundary_v1(state_dir=tmp_state, binding=binding)
    res = run_full_core_okx_injected_exchange_reconciliation_v1(
        identity=ident,
        binding=binding,
        read_only_get_transport=FixtureBackedOkxReadOnlyTransport(fixture),
        pretrade_decision_id="pretrade-terminal",
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
        state_dir=tmp_state,
        apply_durable_state=True,
    )
    st = load_full_core_atomic_authorization_state_v1(
        state_dir=tmp_state, consumption_key=binding.consumption_key()
    )
    assert res.decision.outcome == OUTCOME_CONFIRMED_FILLED
    assert st is not None
    assert st.state == STATE_TERMINAL_RECONCILED
