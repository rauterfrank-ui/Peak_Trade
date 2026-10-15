"""Offline regression tests for Owner-scoped cumulative GET budget enforcement."""

from __future__ import annotations

import json
import multiprocessing
import threading
from pathlib import Path
from unittest import mock

import pytest

from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    collect_fresh_pretrade_runtime_get_v1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    AUTHORIZED_HOST,
    FullCoreProductiveReadOnlyGetError,
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.owner_scoped_get_budget_enforcement_v1.constants_v1 import (
    GRANT_STATE_EXHAUSTED,
    RESERVATION_OUTCOME_COMPLETED,
)
from src.ops.owner_scoped_get_budget_enforcement_v1.durable_ledger_v1 import (
    atomic_pre_send_reserve_v1,
    finalize_reservation_v1,
    load_owner_scoped_get_budget_ledger_v1,
    mint_owner_scoped_get_budget_grant_v1,
    prove_grant_does_not_authorize_post_v1,
)
from src.ops.owner_scoped_get_budget_enforcement_v1.enforcer_v1 import (
    OwnerScopedGetBudgetEnforcerV1,
    OwnerScopedGetBudgetGrantContextV1,
)
from src.ops.owner_scoped_get_budget_enforcement_v1.errors_v1 import OwnerScopedGetBudgetError
from src.ops.owner_scoped_get_budget_enforcement_v1.grant_identity_v1 import (
    OwnerScopedGetBudgetGrantBindingV1,
    compute_owner_grant_identity_digest_v1,
)
from src.ops.pl_tf_002_productive_read_only_get_complete_v1.constants_v1 import (
    FRESH_PRETRADE_INST_TYPE,
    FRESH_PRETRADE_TD_MODE,
    FRESH_PRETRADE_VENUE_INST_ID,
)


def _binding(*, budget: int = 4, wp: str = "TEST_WP") -> OwnerScopedGetBudgetGrantBindingV1:
    return OwnerScopedGetBudgetGrantBindingV1(
        owner_go="OWNER_GO_TEST",
        work_package_id=wp,
        origin_main_sha="4b222dc532bb7229a3d13db8f3b159e97744cbf9",
        cumulative_request_budget=budget,
        authorized_host=AUTHORIZED_HOST,
    )


def _mint(
    tmp_path: Path, *, budget: int = 4, wp: str = "TEST_WP"
) -> OwnerScopedGetBudgetGrantContextV1:
    return OwnerScopedGetBudgetGrantContextV1.mint_v1(
        store_root=tmp_path,
        binding=_binding(budget=budget, wp=wp),
    )


class _FakeHttpResponse:
    def __init__(self, *, status: int = 200, body: bytes, url: str) -> None:
        self.status = status
        self._body = body
        self.url = url

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _okx_json_payload() -> bytes:
    return json.dumps({"code": "0", "data": [{"uid": "1"}]}).encode("utf-8")


def _mp_reserve_finalize_batch(store: str, grant_id: str, worker_id: int) -> None:
    for idx in range(2):
        rid = f"res-{worker_id}-{idx}"
        atomic_pre_send_reserve_v1(
            store_root=store,
            grant_id=grant_id,
            reservation_id=rid,
            endpoint_path="/api/v5/account/config",
        )
        finalize_reservation_v1(
            store_root=store,
            grant_id=grant_id,
            reservation_id=rid,
            outcome=RESERVATION_OUTCOME_COMPLETED,
        )


def test_one_process_stays_within_budget(tmp_path: Path) -> None:
    ctx = _mint(tmp_path, budget=2)
    enforcer = OwnerScopedGetBudgetEnforcerV1(grant_context=ctx)
    transport = FullCoreProductiveReadOnlyGetTransportV1(
        owner_scoped_get_budget_enforcer=enforcer,
        max_request_count=16,
    )
    body = _okx_json_payload()

    def _open(req, timeout=0):
        return _FakeHttpResponse(status=200, body=body, url=req.full_url)

    with mock.patch(
        "src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1.build_opener"
    ) as bo:
        bo.return_value.open.side_effect = _open
        transport.get(
            endpoint="/api/v5/account/config",
            auth_required=False,
            pretrade_decision_id="t1",
        )
        transport.get(
            endpoint="/api/v5/account/balance",
            auth_required=False,
            pretrade_decision_id="t1",
        )
    snap = enforcer.ledger_snapshot_v1()
    assert snap["committed_request_count"] == 2


def test_multiple_processes_share_one_grant(tmp_path: Path) -> None:
    ctx = _mint(tmp_path, budget=4)
    grant_id = ctx.grant_id
    store = str(tmp_path)

    p1 = multiprocessing.Process(target=_mp_reserve_finalize_batch, args=(store, grant_id, 1))
    p2 = multiprocessing.Process(target=_mp_reserve_finalize_batch, args=(store, grant_id, 2))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    assert p1.exitcode == 0
    assert p2.exitcode == 0
    loaded = load_owner_scoped_get_budget_ledger_v1(store_root=store, grant_id=grant_id)
    record = loaded["record"]
    assert int(record["committed_request_count"]) == 4
    assert record["state"] == GRANT_STATE_EXHAUSTED


def test_exhausted_grant_blocks_further_reserve(tmp_path: Path) -> None:
    ctx = _mint(tmp_path, budget=1)
    enforcer = OwnerScopedGetBudgetEnforcerV1(grant_context=ctx)
    r1 = enforcer.begin_get_v1(endpoint_path="/api/v5/account/config")
    enforcer.mark_completed_v1(r1)
    with pytest.raises(OwnerScopedGetBudgetError, match="EXCEEDED|EXHAUSTED"):
        enforcer.begin_get_v1(endpoint_path="/api/v5/account/balance")


def test_crash_after_reservation_counts_against_budget(tmp_path: Path) -> None:
    ctx = _mint(tmp_path, budget=2)
    grant_id = ctx.grant_id
    atomic_pre_send_reserve_v1(
        store_root=tmp_path,
        grant_id=grant_id,
        reservation_id="orphan",
        endpoint_path="/api/v5/account/config",
    )
    loaded = load_owner_scoped_get_budget_ledger_v1(store_root=tmp_path, grant_id=grant_id)
    assert int(loaded["record"]["in_flight_request_count"]) == 1
    enforcer = OwnerScopedGetBudgetEnforcerV1(grant_context=ctx)
    r2 = enforcer.begin_get_v1(endpoint_path="/api/v5/account/balance")
    enforcer.mark_completed_v1(r2)
    with pytest.raises(OwnerScopedGetBudgetError):
        enforcer.begin_get_v1(endpoint_path="/api/v5/public/instruments")


def test_uncertain_wire_fail_closed(tmp_path: Path) -> None:
    ctx = _mint(tmp_path, budget=4)
    enforcer = OwnerScopedGetBudgetEnforcerV1(grant_context=ctx)
    transport = FullCoreProductiveReadOnlyGetTransportV1(
        owner_scoped_get_budget_enforcer=enforcer,
        max_request_count=16,
    )

    def _timeout(req, timeout=0):
        raise TimeoutError("wire-timeout")

    with mock.patch(
        "src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1.build_opener"
    ) as bo:
        bo.return_value.open.side_effect = _timeout
        with pytest.raises(FullCoreProductiveReadOnlyGetError, match="UNCERTAIN_WIRE"):
            transport.get(
                endpoint="/api/v5/account/config",
                auth_required=False,
                pretrade_decision_id="t-timeout",
            )
    snap = enforcer.ledger_snapshot_v1()
    assert int(snap["uncertain_request_count"]) == 1


def test_different_grants_isolated(tmp_path: Path) -> None:
    a = _mint(tmp_path, budget=1, wp="WP_A")
    b = _mint(tmp_path, budget=1, wp="WP_B")
    assert a.grant_id != b.grant_id
    ra = OwnerScopedGetBudgetEnforcerV1(grant_context=a).begin_get_v1(
        endpoint_path="/api/v5/account/config"
    )
    OwnerScopedGetBudgetEnforcerV1(grant_context=a).mark_completed_v1(ra)
    rb = OwnerScopedGetBudgetEnforcerV1(grant_context=b).begin_get_v1(
        endpoint_path="/api/v5/account/config"
    )
    OwnerScopedGetBudgetEnforcerV1(grant_context=b).mark_completed_v1(rb)


def test_grant_identity_stable() -> None:
    b1 = _binding()
    b2 = _binding()
    assert compute_owner_grant_identity_digest_v1(b1) == compute_owner_grant_identity_digest_v1(b2)


def test_no_post_authorization_standing() -> None:
    proof = prove_grant_does_not_authorize_post_v1()
    assert proof["POST_ALLOWED"] == "false"


def test_ledger_record_has_no_secret_markers(tmp_path: Path) -> None:
    ctx = _mint(tmp_path)
    loaded = load_owner_scoped_get_budget_ledger_v1(store_root=tmp_path, grant_id=ctx.grant_id)
    blob = json.dumps(loaded["record"]).lower()
    assert "apikey" not in blob
    assert "passphrase" not in blob


class _FakeFreshPretradeTransport:
    """Minimal GET-only fake for F1 collector compatibility (no wire)."""

    transport_class = "FULL_CORE_PRODUCTIVE_READ_ONLY_GET_V1"

    def __init__(self, *, enforcer: OwnerScopedGetBudgetEnforcerV1 | None) -> None:
        self._enforcer = enforcer
        self.request_count = 0
        self.methods_used: list[str] = []

    def get(self, *, endpoint: str, auth_required: bool, pretrade_decision_id: str, **kwargs):
        from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
            FreshPretradeGetTransportResultV1,
            METHOD_GET,
        )

        path = str(endpoint).split("?", 1)[0]
        reservation = None
        if self._enforcer is not None:
            reservation = self._enforcer.begin_get_v1(endpoint_path=path)
        self.request_count += 1
        self.methods_used.append(METHOD_GET)
        if reservation is not None and self._enforcer is not None:
            self._enforcer.mark_completed_v1(reservation)
        return FreshPretradeGetTransportResultV1(
            get_performed=True,
            method=METHOD_GET,
            endpoint=endpoint,
            http_status=200,
            payload={"code": "0", "data": [{"uid": "1", "instId": "ETH-USDT-SWAP"}]},
            auth_header_sent=auth_required,
            transport_class=self.transport_class,
            venue_live_contact=True,
            historical_reuse=False,
            error_class="",
            body_sha256="abc",
        )


def test_f1_collector_compatible_with_nine_get_budget(tmp_path: Path) -> None:
    ctx = _mint(tmp_path, budget=9)
    enforcer = OwnerScopedGetBudgetEnforcerV1(grant_context=ctx)
    transport = _FakeFreshPretradeTransport(enforcer=enforcer)
    evidence = collect_fresh_pretrade_runtime_get_v1(
        pretrade_decision_id="f1-budget-test",
        instrument_id=FRESH_PRETRADE_VENUE_INST_ID,
        td_mode=FRESH_PRETRADE_TD_MODE,
        inst_type=FRESH_PRETRADE_INST_TYPE,
        transport=transport,
        require_collection=True,
    )
    assert transport.request_count == 9
    assert evidence.get_performed is True
    snap = enforcer.ledger_snapshot_v1()
    assert int(snap["committed_request_count"]) == 9


def test_unauthorized_grant_reuse_wrong_store(tmp_path: Path, tmp_path_factory) -> None:
    ctx = _mint(tmp_path, budget=2)
    other = tmp_path_factory.mktemp("other")
    with pytest.raises(OwnerScopedGetBudgetError, match="ABSENT"):
        atomic_pre_send_reserve_v1(
            store_root=other,
            grant_id=ctx.grant_id,
            reservation_id="x",
            endpoint_path="/api/v5/account/config",
        )


def test_concurrent_reserve_respects_budget(tmp_path: Path) -> None:
    ctx = _mint(tmp_path, budget=3)
    grant_id = ctx.grant_id
    errors: list[str] = []
    lock = threading.Lock()

    def _thread_work(tid: int) -> None:
        try:
            for idx in range(2):
                rid = f"t{tid}-{idx}"
                atomic_pre_send_reserve_v1(
                    store_root=tmp_path,
                    grant_id=grant_id,
                    reservation_id=rid,
                    endpoint_path="/api/v5/account/config",
                )
                finalize_reservation_v1(
                    store_root=tmp_path,
                    grant_id=grant_id,
                    reservation_id=rid,
                    outcome=RESERVATION_OUTCOME_COMPLETED,
                )
        except OwnerScopedGetBudgetError as exc:
            with lock:
                errors.append(str(exc))

    threads = [threading.Thread(target=_thread_work, args=(i,)) for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    loaded = load_owner_scoped_get_budget_ledger_v1(store_root=tmp_path, grant_id=grant_id)
    assert int(loaded["record"]["committed_request_count"]) <= 3
    assert errors


def _tier_a_worker(
    store: str,
    budget: int,
    get_count: int,
    worker_id: int,
    wire_attempts: multiprocessing.Value,
) -> None:
    binding = OwnerScopedGetBudgetGrantBindingV1(
        owner_go="OWNER_GO_TEST",
        work_package_id="TIER_A_WP",
        origin_main_sha="4b222dc532bb7229a3d13db8f3b159e97744cbf9",
        cumulative_request_budget=budget,
        authorized_host=AUTHORIZED_HOST,
    )
    ctx = OwnerScopedGetBudgetGrantContextV1.mint_v1(store_root=Path(store), binding=binding)
    enforcer = OwnerScopedGetBudgetEnforcerV1(grant_context=ctx)
    transport = FullCoreProductiveReadOnlyGetTransportV1(
        owner_scoped_get_budget_enforcer=enforcer,
        max_request_count=16,
    )
    body = _okx_json_payload()

    def _open(req, timeout=0):
        with wire_attempts.get_lock():
            wire_attempts.value += 1
        return _FakeHttpResponse(status=200, body=body, url=req.full_url)

    with mock.patch(
        "src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1.build_opener"
    ) as bo:
        bo.return_value.open.side_effect = _open
        endpoints = (
            "/api/v5/account/config",
            "/api/v5/account/balance",
            "/api/v5/public/instruments",
        )
        for idx in range(get_count):
            transport.get(
                endpoint=endpoints[idx % len(endpoints)],
                auth_required=False,
                pretrade_decision_id=f"tier-a-{worker_id}-{idx}",
            )


def test_tier_a_cumulative_budget_four_processes_fifth_blocked(tmp_path: Path) -> None:
    """OWNER_BUDGET=4 with process GET counts 1+2+1; fifth attempt blocked pre-wire."""
    store = str(tmp_path)
    wire_attempts = multiprocessing.Value("i", 0)
    workers = [
        multiprocessing.Process(target=_tier_a_worker, args=(store, 4, 1, 1, wire_attempts)),
        multiprocessing.Process(target=_tier_a_worker, args=(store, 4, 2, 2, wire_attempts)),
        multiprocessing.Process(target=_tier_a_worker, args=(store, 4, 1, 3, wire_attempts)),
    ]
    for proc in workers:
        proc.start()
    for proc in workers:
        proc.join()
        assert proc.exitcode == 0
    assert int(wire_attempts.value) == 4

    ctx = _mint(tmp_path, budget=4, wp="TIER_A_WP")
    enforcer = OwnerScopedGetBudgetEnforcerV1(grant_context=ctx)
    transport = FullCoreProductiveReadOnlyGetTransportV1(
        owner_scoped_get_budget_enforcer=enforcer,
        max_request_count=16,
    )

    def _open_should_not_run(req, timeout=0):
        raise AssertionError("NO_NETWORK_SEND_ON_FIFTH")

    with mock.patch(
        "src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1.build_opener"
    ) as bo:
        bo.return_value.open.side_effect = _open_should_not_run
        with pytest.raises(FullCoreProductiveReadOnlyGetError):
            transport.get(
                endpoint="/api/v5/account/config",
                auth_required=False,
                pretrade_decision_id="tier-a-fifth",
            )
    loaded = load_owner_scoped_get_budget_ledger_v1(store_root=tmp_path, grant_id=ctx.grant_id)
    assert int(loaded["record"]["committed_request_count"]) == 4
    assert loaded["record"]["state"] == GRANT_STATE_EXHAUSTED


def test_timeout_without_enforcer_preserves_legacy_result() -> None:
    transport = FullCoreProductiveReadOnlyGetTransportV1(max_request_count=16)

    def _timeout(req, timeout=0):
        raise TimeoutError("wire-timeout")

    with mock.patch(
        "src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1.build_opener"
    ) as bo:
        bo.return_value.open.side_effect = _timeout
        result = transport.get(
            endpoint="/api/v5/account/config",
            auth_required=False,
            pretrade_decision_id="legacy-timeout",
        )
    assert result.error_class == "TIMEOUT"
    assert result.get_performed is False


def test_concurrent_mint_same_binding(tmp_path: Path) -> None:
    binding = _binding(wp="CONCURRENT_MINT")
    errors: list[str] = []

    def _mint_worker() -> None:
        try:
            mint_owner_scoped_get_budget_grant_v1(store_root=tmp_path, binding=binding)
        except OwnerScopedGetBudgetError as exc:
            errors.append(str(exc))

    threads = [threading.Thread(target=_mint_worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    first = mint_owner_scoped_get_budget_grant_v1(store_root=tmp_path, binding=binding)
    assert first["created"] is False


def test_mint_is_idempotent_same_binding(tmp_path: Path) -> None:
    binding = _binding()
    first = mint_owner_scoped_get_budget_grant_v1(store_root=tmp_path, binding=binding)
    second = mint_owner_scoped_get_budget_grant_v1(store_root=tmp_path, binding=binding)
    assert first["created"] is True
    assert second["created"] is False
    assert first["grant_id"] == second["grant_id"]
