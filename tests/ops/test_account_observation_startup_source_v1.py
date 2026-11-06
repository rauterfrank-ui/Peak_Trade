"""Injected acquisition → existing collector → real startup consumer/document."""

from contextlib import contextmanager
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit
from unittest.mock import patch

import pytest

from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    FreshPretradeGetTransportResultV1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.constants_v1 import CREDENTIAL_CLASS
from src.ops.okx_eea_private_account_state_runtime_v1.credentials_v1 import (
    join_observation_credential_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.startup_source_v1 import (
    AccountObservationSourceV1,
    open_account_observation_source_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.startup_portfolio_document_v1 import (
    read_startup_portfolio_document_v1,
)
from tests.ops.test_portfolio_budget_host_v1 import _fetch
from tests.ops.test_observed_cap24_start_binding_v1 import state, component, kwargs, tree_bytes

ACCOUNT = "injected-observer-account"
NATIVE = "ADA-USDT-SWAP"
CANONICAL = "instrument-ada"


def credential():
    return join_observation_credential_v1(
        secretref_uri="injected-observer-reference",
        secretref_bound=True,
        credential_class=CREDENTIAL_CLASS,
    )


class InjectedTransport:
    def __init__(self, *, fetch=None, fault=None):
        self.fetch = fetch or _fetch(uid=ACCOUNT)
        self.fault = fault
        self.calls = []

    def get(self, **request):
        self.calls.append(request)
        url = urlsplit(request["endpoint"])
        payload = (
            {"code": "0", "data": []}
            if url.path == "/api/v5/trade/orders-algo-pending"
            else self.fetch(url.path, dict(parse_qsl(url.query)))
        )
        result = FreshPretradeGetTransportResultV1(
            get_performed=True,
            method="GET",
            endpoint=request["endpoint"],
            http_status=200,
            payload=payload,
            auth_header_sent=True,
            transport_class="injected-test-observer",
            venue_live_contact=True,
            historical_reuse=False,
            error_class="",
            body_sha256=hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
        )
        return self.fault(result) if self.fault else result


def source(*, transport=None, clock=lambda: 1000, cred=None):
    return AccountObservationSourceV1(
        credential=cred or credential(),
        transport=transport or InjectedTransport(),
        expected_account_identity=ACCOUNT,
        session_id="injected-start",
        clock=clock,
    )


@pytest.mark.parametrize("quantity", [None, "2", "-2"])
def test_actual_collector_exports_signed_book_into_existing_reader(tmp_path, quantity):
    rows = [] if quantity is None else [{"instId": NATIVE, "posSide": "net", "pos": quantity}]
    transport = InjectedTransport(fetch=_fetch(uid=ACCOUNT, positions=rows))
    observer = source(transport=transport)
    target = tmp_path / "startup.json"
    observed = observer.export_startup_document_v1(
        target, instrument_ids_by_native_id={NATIVE: CANONICAL}
    )
    loaded = read_startup_portfolio_document_v1(
        target, expected_account_identity=ACCOUNT, now_unix=1000
    )
    assert loaded.positions == observed.observed.positions
    assert loaded.event_time_unix == 1000 and loaded.wall_time_unix == 1000
    assert [str(p.signed_quantity) for p in loaded.positions] == (
        [] if quantity is None else [quantity]
    )
    assert target.stat().st_mode & 0o777 == 0o600
    assert len(transport.calls) == 10
    assert all(
        c["auth_required"] is True
        and c["get_cache_policy"] == GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED
        for c in transport.calls
    )
    assert all("instId" not in c["endpoint"] for c in transport.calls)
    assert not list(tmp_path.glob(".startup-observation-*"))
    assert not list(tmp_path.rglob("*.sqlite*"))


@pytest.mark.parametrize(
    "field,value",
    [
        ("get_performed", False),
        ("method", "POST"),
        ("endpoint", "/wrong"),
        ("http_status", 401),
        ("auth_header_sent", False),
        ("venue_live_contact", False),
        ("historical_reuse", True),
        ("error_class", "TIMEOUT"),
        ("body_sha256", ""),
    ],
)
def test_invalid_transport_evidence_cannot_publish_empty_book(tmp_path, field, value):
    observer = source(transport=InjectedTransport(fault=lambda r: replace(r, **{field: value})))
    with pytest.raises(ValueError, match="GET_EVIDENCE_INVALID"):
        observer.export_startup_document_v1(
            tmp_path / "startup.json", instrument_ids_by_native_id={NATIVE: CANONICAL}
        )
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "fault",
    [
        "wrong-account",
        "missing-uid",
        "pending",
        "foreign",
        "duplicate",
        "malformed",
        "continuation",
        "venue-error",
        "stale",
    ],
)
def test_source_and_collector_failures_leave_no_document(tmp_path, fault):
    fetch = _fetch(
        uid="other" if fault == "wrong-account" else None if fault == "missing-uid" else ACCOUNT,
        pending=fault == "pending",
        positions=(
            [{"instId": "FOREIGN", "posSide": "net", "pos": "1"}]
            if fault == "foreign"
            else [{"instId": NATIVE, "posSide": "net", "pos": "1"}] * 2
            if fault == "duplicate"
            else []
        ),
    )

    def mutate(result):
        if fault == "malformed":
            return replace(result, payload={"code": "0", "data": None})
        if fault == "continuation":
            return replace(result, payload={**result.payload, "nextPage": "unread"})
        if fault == "venue-error":
            return replace(result, payload={"code": "50000", "data": []})
        return result

    ticks = iter([1000, 1006]) if fault == "stale" else None
    observer = source(
        transport=InjectedTransport(fetch=fetch, fault=mutate),
        clock=(lambda: next(ticks)) if ticks else lambda: 1000,
    )
    with pytest.raises(ValueError):
        observer.export_startup_document_v1(
            tmp_path / "startup.json", instrument_ids_by_native_id={NATIVE: CANONICAL}
        )
    assert list(tmp_path.iterdir()) == []


def test_failed_late_freshness_validation_removes_temporary_file(tmp_path):
    ticks = iter([1000, 1001, 1007])
    observer = source(clock=lambda: next(ticks))
    with pytest.raises(ValueError, match="STALE_OR_FUTURE"):
        observer.export_startup_document_v1(
            tmp_path / "startup.json", instrument_ids_by_native_id={}
        )
    assert list(tmp_path.iterdir()) == []


def test_no_overwrite_or_symlink_and_concurrent_destination_is_preserved(tmp_path):
    existing = tmp_path / "existing.json"
    existing.write_text("keep")
    observer = source()
    with pytest.raises(ValueError, match="TARGET_EXISTS"):
        observer.export_startup_document_v1(existing, instrument_ids_by_native_id={})
    link = tmp_path / "link"
    link.symlink_to(tmp_path / "absent")
    with pytest.raises(ValueError, match="TARGET_EXISTS"):
        observer.export_startup_document_v1(link, instrument_ids_by_native_id={})
    target = tmp_path / "racing.json"

    def racing_link(_src, dest):
        Path(dest).write_text("concurrent")
        raise FileExistsError()

    with patch(
        "src.ops.okx_eea_private_account_state_runtime_v1.startup_source_v1.os.link",
        side_effect=racing_link,
    ):
        with pytest.raises(FileExistsError):
            observer.export_startup_document_v1(target, instrument_ids_by_native_id={})
    assert target.read_text() == "concurrent" and existing.read_text() == "keep"
    assert not list(tmp_path.glob(".startup-observation-*"))


@pytest.mark.parametrize(
    "path,params",
    [
        ("/api/v5/trade/order", {}),
        ("/api/v5/asset/transfer", {}),
        ("https://eea.okx.com/api/v5/account/config", {}),
        ("/api/v5/account/positions", {"instType": "FUTURES"}),
        ("/api/v5/account/positions", {"instType": "SWAP", "instId": NATIVE}),
    ],
)
def test_account_read_scope_cannot_be_filtered_or_expanded(path, params):
    transport = InjectedTransport()
    with pytest.raises(ValueError):
        source(transport=transport)(path, params)
    assert transport.calls == []


@pytest.mark.parametrize(
    "changes", [{"rest_post_authority": True}, {"signing_capable": False}, {"k2_present": True}]
)
def test_invalid_credential_capability_is_rejected_before_get(changes):
    transport = InjectedTransport()
    with pytest.raises(ValueError, match="CREDENTIAL_SCOPE_INVALID"):
        source(transport=transport, cred=replace(credential(), **changes))
    assert transport.calls == []


def test_trade_credential_class_has_no_fallback():
    cred = credential()
    with pytest.raises(ValueError, match="TRADE_CREDENTIAL_CLASS_FORBIDDEN"):
        source(
            cred=replace(
                cred, identity=replace(cred.identity, credential_class="OKX_EEA_TRADE_API_KEY")
            )
        )


def test_provider_lifetime_covers_source_and_cleanup_on_failure():
    released = []

    @contextmanager
    def provider():
        try:
            yield credential(), InjectedTransport()
        finally:
            released.append(True)

    with pytest.raises(RuntimeError, match="consumer failed"):
        with open_account_observation_source_v1(
            session_provider=provider,
            expected_account_identity=ACCOUNT,
            session_id="injected-session",
            clock=lambda: 1000,
        ) as observer:
            assert observer.collect_v1(instrument_ids_by_native_id={}).account == ACCOUNT
            raise RuntimeError("consumer failed")
    assert released == [True]
    with pytest.raises(ValueError, match="SESSION_CLOSED"):
        observer("/api/v5/account/config", {})
    with pytest.raises(ValueError, match="PROVIDER_REQUIRED"):
        with open_account_observation_source_v1(
            session_provider=None, expected_account_identity=ACCOUNT, session_id="test"
        ):
            pytest.fail("no provider must never enter")


def test_adapter_reaches_actual_n1_cap24_gate_and_preserves_nonflat_state(state):
    from src.ops.n1_standing_pre_external_runtime_supervisor_v1.startup_binding_v1 import (
        acquire_account_bound_n1_startup_v1,
    )
    from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
        PORTFOLIO_STATE_FILENAME,
    )
    from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import PositionTruthV1
    from tests.ops.test_observed_cap24_start_binding_v1 import observed

    chain, prod = state
    pos = PositionTruthV1.from_signed(instrument_id=chain["instrument_id"], signed_quantity="-2")
    recon = prod / "runtime_state/recon"
    (recon / PORTFOLIO_STATE_FILENAME).write_text(
        json.dumps(observed(state, positions=(pos,)).to_dict())
    )
    epoch = component._binding_epoch_unix_v1(chain["binding_epoch"])
    observer = source(
        transport=InjectedTransport(
            fetch=_fetch(
                uid=ACCOUNT,
                positions=[{"instId": chain["venue_native_id"], "posSide": "net", "pos": "-2"}],
            )
        ),
        clock=lambda: epoch,
    )
    selection_before = tree_bytes(prod / "runtime_state/selection")
    result = acquire_account_bound_n1_startup_v1(
        **kwargs(state),
        expected_account_identity=ACCOUNT,
        session_id="adapter-to-cap24",
        private_rest_fetch=observer,
        clock=lambda: epoch,
    )
    assert result.observation.observed.positions[0].signed_quantity == -2
    assert result.handoff.instrument_id == chain["instrument_id"]
    assert tree_bytes(prod / "runtime_state/selection") == selection_before
    assert not list(prod.rglob("*.sqlite*"))


def test_adapter_drives_existing_durable_owner_recovery_and_fences_failed_refresh(tmp_path):
    from tests.ops.test_durable_portfolio_budget_recovery_v1 import (
        ACCOUNT as durable_account,
        BINDINGS,
        EPOCH,
        NOW,
        _produce,
        _reserve,
    )
    from tests.ops.test_portfolio_budget_host_v1 import _host

    transport = InjectedTransport(fetch=_fetch(uid=durable_account))
    observer = AccountObservationSourceV1(
        credential=credential(),
        transport=transport,
        expected_account_identity=durable_account,
        session_id="adapter-budget-recovery",
        clock=lambda: NOW,
    )
    host = _host(tmp_path, observer, clock=lambda: NOW, expected_account=durable_account)
    try:
        context = host.observe_v1(BINDINGS)
        assert context.observed.source_id == "host-private-rest-swap"
        context.recover_v1(host.owner, _produce(epoch=EPOCH))
        reservation = _reserve(host.owner).reservation
        amount = host.owner.active_sum_v1()
        assert amount > 0
        transport.fetch = _fetch(uid="wrong-account")
        with pytest.raises(ValueError, match="ACCOUNT_MISMATCH"):
            host.observe_v1(BINDINGS)
        assert host.owner.budget_state_v1().recovery_required
        assert host.owner.active_sum_v1() == amount
        assert reservation.reservation_id
        assert host.owner.stored_reservation_count_v1() == 1
    finally:
        host.close()
        observer.close()


def test_existing_private_restart_widens_legacy_instrument_filter(tmp_path):
    from src.ops.n1_whole_system_hard_facts_integration_wp_v1.private_observation_chain_v1 import (
        prove_private_restart_recovery_order_v1,
        private_restart_reconciliation_trusted_v1,
    )

    transport = InjectedTransport()
    observer = source(transport=transport)
    result = prove_private_restart_recovery_order_v1(
        store_root=tmp_path / "private",
        rest_fetch_json=observer,
    )
    assert private_restart_reconciliation_trusted_v1(result)
    assert len(transport.calls) == 10
    assert all("instId" not in item["endpoint"] for item in transport.calls)
    transport.fetch = _fetch(uid=ACCOUNT, pending=True)
    with pytest.raises(ValueError, match="PENDING_ORDERS_UNRESOLVED"):
        observer("/api/v5/trade/orders-pending", {"instType": "SWAP", "instId": "ETH-USDT-SWAP"})
    assert transport.calls[-1]["endpoint"] == "/api/v5/trade/orders-pending?instType=SWAP"


@pytest.mark.parametrize("kind", ["conditional", "oco", "trigger", "move_order_stop"])
def test_untriggered_algos_block_export_even_when_ordinary_book_is_empty(tmp_path, kind):
    def inject(result):
        if (
            "orders-algo-pending" in result.endpoint
            and dict(parse_qsl(urlsplit(result.endpoint).query))["ordType"] == kind
        ):
            return replace(
                result, payload={"code": "0", "data": [{"algoId": "open-algo", "instId": NATIVE}]}
            )
        return result

    observer = source(transport=InjectedTransport(fault=inject))
    with pytest.raises(ValueError, match="PENDING_ALGO_ORDERS_UNRESOLVED"):
        observer.export_startup_document_v1(
            tmp_path / "startup.json", instrument_ids_by_native_id={}
        )
    assert list(tmp_path.iterdir()) == []


def test_unavailable_algo_read_is_not_an_empty_book(tmp_path):
    def inject(result):
        if "orders-algo-pending" in result.endpoint:
            return replace(result, http_status=403, get_performed=False)
        return result

    with pytest.raises(ValueError, match="GET_EVIDENCE_INVALID"):
        source(transport=InjectedTransport(fault=inject)).export_startup_document_v1(
            tmp_path / "startup.json", instrument_ids_by_native_id={}
        )
    assert list(tmp_path.iterdir()) == []
