"""Actual K1 parse/sign/GET → collector/export, with injected OS and HTTP only."""

from contextlib import contextmanager
import io
import json
from pathlib import Path
from unittest.mock import patch
from urllib.request import HTTPSHandler, ProxyHandler, Request, build_opener
from urllib.response import addinfourl
from urllib.parse import parse_qsl, urlsplit
from email.message import Message

import pytest

from src.ops.full_core_live_path_composition_root_v1 import (
    productive_read_only_get_transport_v1 as wire,
)
from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
    K1_ACCOUNT_READ_PROFILE,
    open_k1_account_observation_source_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.startup_portfolio_document_v1 import (
    read_startup_portfolio_document_v1,
)
from tests.ops.test_current_productive_governed_live_c1_get_only_fresh_pretrade_transport_bind_v1 import (
    _FakeKeychainBackend,
)
from tests.ops.test_portfolio_budget_host_v1 import _fetch

ACCOUNT = "injected-k1-account"


class InjectedOpener:
    def __init__(self, *, account=ACCOUNT, positions=(), pending=False, algo_pending=False):
        self.fetch = _fetch(uid=account, positions=positions)
        self.pending = pending
        self.algo_pending = algo_pending
        self.requests = []

    @contextmanager
    def open(self, req, timeout):
        assert req.get_method() == "GET"
        assert urlsplit(req.full_url).hostname == "eea.okx.com"
        assert req.has_header("Ok-access-sign")
        self.requests.append(req.full_url)
        url = urlsplit(req.full_url)
        query = dict(parse_qsl(url.query))
        payload = (
            {"code": "0", "data": [{"instType": "FUTURES"}] if self.algo_pending else []}
            if url.path.endswith("orders-algo-pending")
            else self.fetch(url.path, query)
        )
        if self.pending and url.path.endswith("/orders-pending") and "instType" not in query:
            payload["data"] = [{"instType": "FUTURES", "instId": "BTC-USD_UM_XPERP-310404"}]

        class Response:
            status = 200
            url = req.full_url

            def read(self):
                return json.dumps(payload).encode()

        yield Response()


def test_k1_profile_exports_actual_signed_source_and_cleans_up(tmp_path):
    opener = InjectedOpener(positions=[{"instId": "ETH-USDT-SWAP", "posSide": "net", "pos": "-2"}])

    def build(*handlers):
        assert any(isinstance(h, wire._RejectAuthenticatedRedirectsV1) for h in handlers)
        return opener

    with patch.object(wire, "build_opener", side_effect=build):
        with open_k1_account_observation_source_v1(
            expected_account_identity=ACCOUNT,
            session_id="injected-k1",
            max_request_count=10,
            k1_lookup_backend=_FakeKeychainBackend(),
            clock=lambda: 1000,
        ) as source:
            assert source.credential_profile == K1_ACCOUNT_READ_PROFILE
            assert not hasattr(source.credential, "identity")  # no fake dedicated credential
            path = tmp_path / "startup.json"
            observed = source.export_startup_document_v1(
                path, instrument_ids_by_native_id={"ETH-USDT-SWAP": "canonical-eth"}
            )
            assert observed.account == ACCOUNT
            parsed = read_startup_portfolio_document_v1(
                path, expected_account_identity=ACCOUNT, now_unix=1000
            )
            assert str(parsed.positions[0].signed_quantity) == "-2"
            assert len(opener.requests) == 10
            with pytest.raises(ValueError, match="ENDPOINT_FORBIDDEN"):
                source.transport.get(endpoint="/api/v5/asset/transfer", auth_required=True)
        with pytest.raises(ValueError, match="SESSION_CLOSED"):
            source("/api/v5/account/config", {})
        assert source.credential is None and source.transport is None


def test_wrong_account_blocks_before_other_private_reads(tmp_path):
    opener = InjectedOpener(account="other")
    with patch.object(wire, "build_opener", return_value=opener):
        with open_k1_account_observation_source_v1(
            expected_account_identity=ACCOUNT,
            session_id="wrong-account",
            max_request_count=10,
            k1_lookup_backend=_FakeKeychainBackend(),
            clock=lambda: 1000,
        ) as source:
            with pytest.raises(ValueError, match="ACCOUNT_MISMATCH"):
                source.export_startup_document_v1(
                    tmp_path / "startup.json", instrument_ids_by_native_id={}
                )
    assert len(opener.requests) == 1
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("expected_account_identity", ""),
        ("session_id", ""),
        ("max_request_count", 9),
        ("max_request_count", True),
        ("inventory_inst_type", "FUTURES"),
        ("inventory_inst_type", "OPTION"),
    ],
)
def test_configuration_denied_before_keychain_lookup(field, value):
    class ForbiddenBackend:
        def copy_matching_generic_password_value_data_v1(self, **kwargs):
            pytest.fail("lookup before validation")

    args = dict(
        expected_account_identity=ACCOUNT,
        session_id="valid",
        max_request_count=10,
        k1_lookup_backend=ForbiddenBackend(),
    )
    args[field] = value
    with pytest.raises(ValueError):
        with open_k1_account_observation_source_v1(**args):
            pytest.fail("unreachable")


def test_redirect_never_forwards_signed_headers_to_second_host():
    hosts = []

    class FakeHTTPS(HTTPSHandler):
        def https_open(self, req):
            hosts.append(urlsplit(req.full_url).hostname)
            assert req.get_header("Ok-access-key") == "sentinel-test-key"
            headers = Message()
            headers["Location"] = "https://foreign.invalid/collect"
            response = addinfourl(io.BytesIO(b""), headers, req.full_url, 302)
            response.msg = "Found"
            return response

    opener = build_opener(ProxyHandler({}), FakeHTTPS(), wire._RejectAuthenticatedRedirectsV1())
    request = Request(
        "https://eea.okx.com/api/v5/account/config", headers={"OK-ACCESS-KEY": "sentinel-test-key"}
    )
    with pytest.raises(wire.FullCoreProductiveReadOnlyGetError, match="REDIRECT_FORBIDDEN"):
        opener.open(request)
    assert hosts == ["eea.okx.com"]


@pytest.mark.parametrize("product,clear", [("SWAP", True), ("FUTURES", False), (None, False)])
def test_scope_probe_exposes_other_or_unknown_products_without_adopting_account(product, clear):
    row = {"instId": "ETH-USDT-SWAP", "posSide": "net", "pos": "1"}
    if product is not None:
        row["instType"] = product
    opener = InjectedOpener(positions=[row])
    with patch.object(wire, "build_opener", return_value=opener):
        with open_k1_account_observation_source_v1(
            expected_account_identity=ACCOUNT,
            session_id="scope-inspection",
            max_request_count=10,
            k1_lookup_backend=_FakeKeychainBackend(),
            clock=lambda: 1000,
        ) as source:
            result = source.inspect_account_scope_v1()
    assert result["supported_scope_clear"] is clear
    assert result["configured_account_matched"] is True
    assert result["capital_admitted"] is False and result["equity_reconstructed"] is False
    assert len(opener.requests) == 7
    assert all("instType" not in url for url in opener.requests)
    assert ACCOUNT not in json.dumps(result)


@pytest.mark.parametrize(
    "fault,expected",
    [
        (None, None),
        ("swap-position", None),
        ("supported-futures-position", None),
        ("swap-in-futures", "ACCOUNT_PRODUCTS_OUTSIDE_CURRENT_FUTURES_CONSUMER"),
        ("futures-position", "ACCOUNT_PRODUCTS_OUTSIDE_CURRENT_SWAP_CONSUMER"),
        ("missing-product", "ACCOUNT_PRODUCTS_OUTSIDE_CURRENT_SWAP_CONSUMER"),
        ("pending", "STARTUP_PENDING_ORDERS_UNRESOLVED"),
        ("algo-pending", "STARTUP_PENDING_ALGO_ORDERS_UNRESOLVED"),
        ("futures-binding", "HOST_BUDGET_BOUND_PRODUCT_SCOPE_UNPROVEN"),
    ],
)
def test_account_inventory_guard_at_original_budget_host(tmp_path, fault, expected):
    from dataclasses import replace

    from tests.ops.test_portfolio_budget_host_v1 import BOUND, _host

    bound = BOUND
    product = "SWAP"
    positions = []
    if fault in {"futures-position", "missing-product"}:
        position = {"instId": "BTC-USD_UM_XPERP-310404", "posSide": "net", "pos": "1"}
        if fault == "futures-position":
            position["instType"] = "FUTURES"
        positions.append(position)
    if fault == "swap-position":
        positions.append(
            {"instId": BOUND.venue_native_id, "instType": "SWAP", "posSide": "net", "pos": "-2"}
        )
    if fault in {"supported-futures-position", "swap-in-futures"}:
        product = "FUTURES"
        bound = replace(
            BOUND,
            instrument_id="okx_eea:linear_dated_future:BTC:USD:USD:btc-usd_um_xperp-310404",
            venue_native_id="BTC-USD_UM_XPERP-310404",
        )
        positions.append(
            {
                "instId": bound.venue_native_id
                if fault == "supported-futures-position"
                else BOUND.venue_native_id,
                "instType": "FUTURES" if fault == "supported-futures-position" else "SWAP",
                "posSide": "net",
                "pos": "-2",
            }
        )
    if fault == "futures-binding":
        bound = replace(BOUND, venue_native_id="BTC-USD_UM_XPERP-310404")
    opener = InjectedOpener(
        positions=positions, pending=fault == "pending", algo_pending=fault == "algo-pending"
    )
    with patch.object(wire, "build_opener", return_value=opener):
        with open_k1_account_observation_source_v1(
            expected_account_identity=ACCOUNT,
            session_id="account-inventory",
            max_request_count=10,
            k1_lookup_backend=_FakeKeychainBackend(),
            account_inventory_guard=True,
            inventory_inst_type=product,
        ) as source:
            if product == "FUTURES":
                with pytest.raises(ValueError, match="LEGACY_STARTUP_DOCUMENT_UNSUPPORTED"):
                    source.export_startup_document_v1(
                        tmp_path / "startup.json", instrument_ids_by_native_id={}
                    )
                assert not opener.requests and not (tmp_path / "startup.json").exists()
            host = _host(tmp_path, source, expected_account=ACCOUNT)
            try:
                if expected is None:
                    result = host.observe_v1({"LANE_1": bound})
                    assert not result.pending_orders
                    assert result.observed.source_id == f"host-private-rest-{product.lower()}"
                    if positions:
                        (position,) = result.observed.positions
                        assert position.instrument_id == bound.instrument_id
                        assert position.signed_quantity == -2
                    else:
                        assert result.observed.positions == ()
                    assert host.owner.budget_state_v1().recovery_required
                    assert len(opener.requests) == 10
                else:
                    with pytest.raises(ValueError, match=expected):
                        host.observe_v1({"LANE_1": bound})
                    assert host.owner is None and not host.root.exists()
                assert source.pending_observation_v1() is None
            finally:
                host.close()

    urls = [urlsplit(request) for request in opener.requests]
    inventory = [
        url
        for url in urls
        if url.path.endswith(("positions", "orders-pending", "orders-algo-pending"))
    ]
    if fault == "futures-binding":
        assert not urls
    else:
        assert inventory and all("instType" not in url.query for url in inventory)
    if expected is None:
        assert len(inventory) == 6
        assert all(
            dict(parse_qsl(url.query)) == {"instType": product}
            for url in urls
            if url.path.endswith(("orders-history", "fills"))
        )


def test_readiness_cli_defaults_to_no_keychain_or_network(monkeypatch, capsys):
    from scripts.ops import run_k1_account_observation_readiness_v1 as cli

    def forbidden(**kwargs):
        pytest.fail("unexpected credential access")

    monkeypatch.setattr(cli, "open_k1_account_observation_source_v1", forbidden)
    assert cli.main(["--expected-account-identity", ACCOUNT]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["mode"] == "CONFIG_ONLY"
    assert not report["keychain_access_attempted"] and report["private_get_attempt_count"] == 0


def test_readiness_cli_real_path_is_bounded_and_sanitized(monkeypatch, tmp_path, capsys):
    from scripts.ops import run_k1_account_observation_readiness_v1 as cli

    @contextmanager
    def injected(**kwargs):
        with open_k1_account_observation_source_v1(
            **kwargs, k1_lookup_backend=_FakeKeychainBackend(), clock=lambda: 1000
        ) as source:
            yield source

    monkeypatch.setattr(cli, "open_k1_account_observation_source_v1", injected)
    target = tmp_path / "readiness.json"
    with patch.object(wire, "build_opener", return_value=InjectedOpener()):
        assert (
            cli.main(
                ["--expected-account-identity", ACCOUNT, "--observe-once", "--output", str(target)]
            )
            == 0
        )
    report = json.loads(capsys.readouterr().out)
    assert report["private_get_attempt_count"] == 7
    assert report["observation"]["configured_account_matched"]
    assert not report["capital_admitted"]
    assert ACCOUNT not in target.read_text()
    assert target.stat().st_mode & 0o777 == 0o600


def test_readiness_cli_redacts_unknown_provider_exception(monkeypatch, capsys):
    from scripts.ops import run_k1_account_observation_readiness_v1 as cli

    def failing(**kwargs):
        raise ValueError("synthetic-credential-must-never-be-printed")

    monkeypatch.setattr(cli, "open_k1_account_observation_source_v1", failing)
    assert cli.main(["--expected-account-identity", ACCOUNT, "--observe-once"]) == 2
    output = capsys.readouterr().out
    assert "synthetic-credential" not in output
    assert json.loads(output)["error_code"] == "K1_SOURCE_READ_FAILED"


@pytest.mark.parametrize(
    "details,status",
    [
        ([], "ABSENT_NOT_ZERO"),
        ([{"ccy": "USDT", "availEq": "2000"}], "ABSENT_NOT_ZERO"),
        ([{"ccy": "USDC", "availEq": "0"}], "OBSERVED_NUMERIC"),
        ([{"ccy": "USDC", "availEq": "25"}], "OBSERVED_NUMERIC"),
        ([{"ccy": "USDC", "availEq": ""}], "NUMERIC_UNPROVEN"),
        ([{"ccy": "USDC", "availEq": "NaN"}], "NUMERIC_UNPROVEN"),
        ([{"ccy": "USDC", "availEq": "1e4"}], "NUMERIC_UNPROVEN"),
        ([{"ccy": "USDC", "availEq": "1"}] * 2, "DUPLICATE_UNPROVEN"),
    ],
)
def test_treasury_source_probe_never_substitutes_currency_or_funding(details, status):
    opener = InjectedOpener()
    original = opener.fetch

    def fetch(path, params):
        if path == "/api/v5/asset/balances":
            return {
                "code": "0",
                "data": [{"ccy": "USDC", "bal": "999", "frozenBal": "0", "availBal": "999"}],
            }
        if path == "/api/v5/account/balance":
            return {"code": "0", "data": [{"totalEq": "99999", "details": details}]}
        return original(path, params)

    opener.fetch = fetch
    with patch.object(wire, "build_opener", return_value=opener):
        with open_k1_account_observation_source_v1(
            expected_account_identity=ACCOUNT,
            session_id="input-probe",
            max_request_count=10,
            k1_lookup_backend=_FakeKeychainBackend(),
            clock=lambda: 1000,
        ) as source:
            result = source.inspect_treasury_inputs_v1()
    assert result["trading_usdc_avail_eq_status"] == status
    assert result["funding_usdc_row_status"] == "PRESENT"
    assert result["inputs_ready"] is (status == "OBSERVED_NUMERIC")
    assert result["capital_admitted"] is False and result["equity_reconstructed"] is False
    assert "99999" not in json.dumps(result) and "999" not in json.dumps(result)
    assert len(opener.requests) == 3


def test_explicit_config_resolves_found_k1_without_lookup(monkeypatch, capsys):
    from scripts.ops import run_k1_account_observation_readiness_v1 as cli
    from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
        load_k1_account_source_config_v1,
    )

    config = Path(__file__).resolve().parents[2] / "config/ops/treasury_k1_account_source_v1.json"
    value = load_k1_account_source_config_v1(config)
    assert value["profile"] == K1_ACCOUNT_READ_PROFILE
    assert value["service_activation_authorized"] is False

    def forbidden(**kwargs):
        pytest.fail("config read must not access Keychain")

    monkeypatch.setattr(cli, "open_k1_account_observation_source_v1", forbidden)
    assert cli.main(["--config", str(config)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["mode"] == "CONFIG_ONLY"
    assert value["expected_account_identity"] not in json.dumps(report)


@pytest.mark.parametrize(
    "field,value",
    [
        ("profile", "UNKNOWN"),
        ("keychain_service", "other"),
        ("service_activation_authorized", True),
        ("max_request_count", True),
        ("expected_account_identity", ""),
    ],
)
def test_changed_config_scope_is_rejected_before_acquisition(tmp_path, field, value):
    from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
        load_k1_account_source_config_v1,
    )

    path = Path(__file__).resolve().parents[2] / "config/ops/treasury_k1_account_source_v1.json"
    data = json.loads(path.read_text())
    data[field] = value
    changed = tmp_path / "config.json"
    changed.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        load_k1_account_source_config_v1(changed)


def test_redirect_failure_consumes_existing_transport_request_quota():
    from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_live_c1_get_only_fresh_pretrade_transport_bind_v1 import (
        open_governed_live_c1_get_only_fresh_pretrade_transport_v1,
    )

    attempts = []

    class RedirectOpener:
        def open(self, req, timeout):
            attempts.append(req.full_url)
            raise wire.FullCoreProductiveReadOnlyGetError("GET_REDIRECT_FORBIDDEN")

    with open_governed_live_c1_get_only_fresh_pretrade_transport_v1(
        max_request_count=1, k1_lookup_backend=_FakeKeychainBackend()
    ) as (transport, _proof):
        with patch.object(wire, "build_opener", return_value=RedirectOpener()):
            with pytest.raises(wire.FullCoreProductiveReadOnlyGetError, match="REDIRECT_FORBIDDEN"):
                transport.get(
                    endpoint="/api/v5/account/config",
                    auth_required=True,
                    pretrade_decision_id="test",
                )
            with pytest.raises(
                wire.FullCoreProductiveReadOnlyGetError, match="MAX_REQUEST_COUNT_EXCEEDED"
            ):
                transport.get(
                    endpoint="/api/v5/account/config",
                    auth_required=True,
                    pretrade_decision_id="test",
                )
        assert transport.request_count == 1
    assert len(attempts) == 1
