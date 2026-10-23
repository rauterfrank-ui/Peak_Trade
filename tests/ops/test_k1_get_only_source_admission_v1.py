"""Offline admission tests for the existing K1 Keychain item."""

from __future__ import annotations

import ast
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from subprocess import CompletedProcess

import pytest

from src.ops.current_read_only_observation_get_path_v1.constants_v1 import (
    AUTHORIZED_HOST,
    CREDENTIAL_CLASS,
    FORBIDDEN_TRADE_CREDENTIAL_CLASS,
    FORBIDDEN_TRADE_SECRETREF_URI,
    K1_GET_KEYCHAIN_ACCESS_CONSUMER,
    K1_GET_KEYCHAIN_ACCESS_OWNER_AUTHORIZATION,
    K1_KEYCHAIN_ACCESS_STANDING_AUTHORIZED,
    K1_KEYCHAIN_ACCOUNT,
    K1_KEYCHAIN_SERVICE,
    K1_SOURCE_CREDENTIAL_CLASS,
    K1_SOURCE_REF_URI,
    NETWORK_SEND_AUTHORIZED,
    POST_ALLOWED,
)
from src.ops.current_read_only_observation_get_path_v1.errors_v1 import (
    ReadOnlyObservationGetError,
)
from src.ops.current_read_only_observation_get_path_v1.handle_v1 import (
    release_read_only_observation_session_v1,
)
from src.ops.current_read_only_observation_get_path_v1.k1_source_admission_v1 import (
    admit_k1_keychain_get_source_v1,
    issue_k1_get_keychain_access_permit_v1,
    load_admitted_k1_get_handle_v1,
    read_named_k1_keychain_opaque_v1,
)
from src.ops.current_read_only_observation_get_path_v1.signer_v1 import (
    build_read_only_observation_get_headers_v1,
)
from src.ops.current_read_only_observation_get_path_v1.transport_v1 import (
    complete_read_only_observation_get_v1,
    prepare_read_only_observation_get_v1,
)

_FIXTURE = (
    b'{"apiKey":"fixture-api-key","secretKey":"fixture-secret-key",'
    b'"passphrase":"fixture-passphrase"}'
)
_LEAK = "LEAK-MARKER-SECRET"
_PACKAGE = Path("src/ops/current_read_only_observation_get_path_v1/k1_source_admission_v1.py")


def _reader(_service: str, _account: str) -> bytes:
    return _FIXTURE


def _calls() -> tuple[list[tuple[str, str]], object]:
    seen: list[tuple[str, str]] = []

    def reader(service: str, account: str) -> bytes:
        seen.append((service, account))
        return _FIXTURE

    return seen, reader


def _admit(reader=_reader, **overrides):
    fields = {
        "keychain_service": K1_KEYCHAIN_SERVICE,
        "keychain_account": K1_KEYCHAIN_ACCOUNT,
        "credential_class": K1_SOURCE_CREDENTIAL_CLASS,
        "opaque_reader": reader,
    }
    fields.update(overrides)
    return admit_k1_keychain_get_source_v1(**fields)


def test_source_identity_is_the_existing_item() -> None:
    assert K1_KEYCHAIN_SERVICE == "peak-trade.full-core.venue-credentials"
    assert K1_KEYCHAIN_ACCOUNT == "okx-eea.productive"
    assert K1_SOURCE_CREDENTIAL_CLASS == "FULL_CORE_VENUE_AUTH_CLASS"
    assert K1_SOURCE_REF_URI == "fullcore-cred://provider-ref/okx-eea-productive"
    assert K1_SOURCE_CREDENTIAL_CLASS != CREDENTIAL_CLASS
    assert POST_ALLOWED is False
    assert NETWORK_SEND_AUTHORIZED is False


def test_wrong_keychain_service_does_not_read() -> None:
    seen, reader = _calls()
    with pytest.raises(ReadOnlyObservationGetError, match="KEYCHAIN_SERVICE_FORBIDDEN"):
        _admit(reader, keychain_service="other.service")
    assert seen == []


def test_wrong_keychain_account_does_not_read() -> None:
    seen, reader = _calls()
    with pytest.raises(ReadOnlyObservationGetError, match="KEYCHAIN_ACCOUNT_FORBIDDEN"):
        _admit(reader, keychain_account="other.account")
    assert seen == []


def test_wrong_credential_class_does_not_read() -> None:
    seen, reader = _calls()
    with pytest.raises(ReadOnlyObservationGetError, match="CREDENTIAL_CLASS_FORBIDDEN"):
        _admit(reader, credential_class=CREDENTIAL_CLASS)
    assert seen == []


def test_trade_and_canary_sources_are_rejected() -> None:
    seen, reader = _calls()
    with pytest.raises(ReadOnlyObservationGetError, match="TRADE_CREDENTIAL_FORBIDDEN"):
        _admit(reader, credential_class=FORBIDDEN_TRADE_CREDENTIAL_CLASS)
    with pytest.raises(ReadOnlyObservationGetError, match="TRADE_CREDENTIAL_FORBIDDEN"):
        _admit(reader, keychain_account=FORBIDDEN_TRADE_SECRETREF_URI)
    assert seen == []


def test_missing_keychain_source() -> None:
    with pytest.raises(ReadOnlyObservationGetError, match="KEYCHAIN_SOURCE_MISSING"):
        _admit(lambda _service, _account: None)
    with pytest.raises(ReadOnlyObservationGetError, match="KEYCHAIN_SOURCE_MISSING"):
        _admit(lambda _service, _account: b"")


def test_malformed_material_does_not_leak() -> None:
    with pytest.raises(ReadOnlyObservationGetError, match="K1_OPAQUE_JSON_MALFORMED") as caught:
        _admit(lambda _service, _account: f"{{{_LEAK}".encode())
    assert _LEAK not in str(caught.value)


@pytest.mark.parametrize("method", ("POST", "PUT", "PATCH", "DELETE"))
def test_admitted_handle_rejects_non_get_methods(method: str) -> None:
    handle = _admit()
    try:
        with pytest.raises(ReadOnlyObservationGetError, match="METHOD_FORBIDDEN"):
            prepare_read_only_observation_get_v1(
                handle=handle,
                endpoint="/api/v5/account/config",
                method=method,
            )
        with pytest.raises(ReadOnlyObservationGetError, match="SIGNER_METHOD_FORBIDDEN"):
            build_read_only_observation_get_headers_v1(
                handle=handle,
                url=f"https://{AUTHORIZED_HOST}/api/v5/account/config",
                method=method,
            )
    finally:
        release_read_only_observation_session_v1(handle)


def test_admitted_handle_rejects_foreign_host_and_endpoint() -> None:
    handle = _admit()
    try:
        with pytest.raises(ReadOnlyObservationGetError, match="HOST_NOT_EEA_OKX"):
            prepare_read_only_observation_get_v1(
                handle=handle,
                endpoint="https://www.okx.com/api/v5/account/config",
            )
        with pytest.raises(ReadOnlyObservationGetError, match="ENDPOINT_FORBIDDEN"):
            prepare_read_only_observation_get_v1(
                handle=handle,
                endpoint="/api/v5/trade/order",
            )
    finally:
        release_read_only_observation_session_v1(handle)


def test_secret_repr_and_network_send_stay_closed() -> None:
    handle = _admit()
    try:
        assert "fixture-secret-key" not in repr(handle)
        assert "fixture-passphrase" not in str(handle)
        prepared = prepare_read_only_observation_get_v1(
            handle=handle,
            endpoint="/api/v5/account/config",
        )
        assert prepared.method == "GET"
        assert prepared.endpoint_path == "/api/v5/account/config"
        assert "fixture-secret-key" not in repr(prepared)
        with pytest.raises(ReadOnlyObservationGetError, match="NETWORK_NOT_AUTHORIZED"):
            complete_read_only_observation_get_v1(prepared=prepared, sender_result=None)
    finally:
        release_read_only_observation_session_v1(handle)


def test_named_reader_refuses_other_items_without_subprocess(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_run(*_args, **_kwargs):
        raise AssertionError("subprocess must not run")

    monkeypatch.setattr(subprocess, "run", fail_run)
    with pytest.raises(ReadOnlyObservationGetError, match="KEYCHAIN_SOURCE_FORBIDDEN"):
        read_named_k1_keychain_opaque_v1("other.service", K1_KEYCHAIN_ACCOUNT)


def test_named_reader_argv_is_exact_and_has_no_secret_dump() -> None:
    source = _PACKAGE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    argv_lists = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.List)
        and any(
            isinstance(elt, ast.Constant) and elt.value == "find-generic-password"
            for elt in node.elts
        )
    ]
    assert len(argv_lists) == 1
    values = [elt.value for elt in argv_lists[0].elts if isinstance(elt, ast.Constant)]
    assert values[:2] == ["security", "find-generic-password"]
    assert "-w" in values
    assert "-g" not in values
    assert "urlopen" not in source


_NOW = datetime(2026, 10, 24, 0, 0, tzinfo=timezone.utc)


def _forbid_subprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_run(*_args, **_kwargs):
        raise AssertionError("subprocess must not run")

    monkeypatch.setattr(subprocess, "run", fail_run)


def _issue(*, now: datetime = _NOW, **overrides):
    fields = {
        "owner_authorization": K1_GET_KEYCHAIN_ACCESS_OWNER_AUTHORIZATION,
        "consumer_id": K1_GET_KEYCHAIN_ACCESS_CONSUMER,
        "keychain_service": K1_KEYCHAIN_SERVICE,
        "keychain_account": K1_KEYCHAIN_ACCOUNT,
        "now": now,
    }
    fields.update(overrides)
    return issue_k1_get_keychain_access_permit_v1(**fields)


def test_missing_authorization_does_not_read(monkeypatch: pytest.MonkeyPatch) -> None:
    _forbid_subprocess(monkeypatch)
    assert K1_KEYCHAIN_ACCESS_STANDING_AUTHORIZED is False
    with pytest.raises(ReadOnlyObservationGetError, match="KEYCHAIN_ACCESS_AUTHORIZATION_MISSING"):
        _issue(owner_authorization="")
    with pytest.raises(ReadOnlyObservationGetError, match="KEYCHAIN_ACCESS_AUTHORIZATION_MISSING"):
        load_admitted_k1_get_handle_v1(
            keychain_service=K1_KEYCHAIN_SERVICE,
            keychain_account=K1_KEYCHAIN_ACCOUNT,
            credential_class=K1_SOURCE_CREDENTIAL_CLASS,
        )


def test_expired_authorization_does_not_read(monkeypatch: pytest.MonkeyPatch) -> None:
    _forbid_subprocess(monkeypatch)
    permit = _issue()
    with pytest.raises(ReadOnlyObservationGetError, match="KEYCHAIN_ACCESS_EXPIRED"):
        read_named_k1_keychain_opaque_v1(
            K1_KEYCHAIN_SERVICE,
            K1_KEYCHAIN_ACCOUNT,
            permit=permit,
            now=_NOW + timedelta(seconds=31),
        )


def test_reused_authorization_reads_once(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_run(argv, **_kwargs):
        calls.append(list(argv))
        return CompletedProcess(argv, 0, stdout=_FIXTURE + b"\n", stderr=b"")

    monkeypatch.setattr(subprocess, "run", fake_run)
    permit = _issue()
    first = read_named_k1_keychain_opaque_v1(
        K1_KEYCHAIN_SERVICE,
        K1_KEYCHAIN_ACCOUNT,
        permit=permit,
        now=_NOW,
    )
    assert first == _FIXTURE
    with pytest.raises(ReadOnlyObservationGetError, match="KEYCHAIN_ACCESS_REUSED"):
        read_named_k1_keychain_opaque_v1(
            K1_KEYCHAIN_SERVICE,
            K1_KEYCHAIN_ACCOUNT,
            permit=permit,
            now=_NOW,
        )
    assert len(calls) == 1


def test_wrong_service_account_and_consumer_do_not_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _forbid_subprocess(monkeypatch)
    with pytest.raises(ReadOnlyObservationGetError, match="KEYCHAIN_SERVICE_FORBIDDEN"):
        _issue(keychain_service="other.service")
    with pytest.raises(ReadOnlyObservationGetError, match="KEYCHAIN_ACCOUNT_FORBIDDEN"):
        _issue(keychain_account="other.account")
    with pytest.raises(ReadOnlyObservationGetError, match="KEYCHAIN_ACCESS_CONSUMER_FORBIDDEN"):
        _issue(consumer_id="PRODUCTIVE_K1_SIGNER")


def test_direct_reader_call_without_permit_does_not_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _forbid_subprocess(monkeypatch)
    with pytest.raises(ReadOnlyObservationGetError, match="KEYCHAIN_ACCESS_AUTHORIZATION_MISSING"):
        read_named_k1_keychain_opaque_v1(K1_KEYCHAIN_SERVICE, K1_KEYCHAIN_ACCOUNT)


def test_permit_repr_and_post_stay_closed() -> None:
    permit = _issue()
    assert "fixture-secret-key" not in repr(permit)
    assert K1_GET_KEYCHAIN_ACCESS_OWNER_AUTHORIZATION not in repr(permit)
    assert POST_ALLOWED is False
    assert NETWORK_SEND_AUTHORIZED is False
    handle = _admit()
    try:
        with pytest.raises(ReadOnlyObservationGetError, match="METHOD_FORBIDDEN"):
            prepare_read_only_observation_get_v1(
                handle=handle,
                endpoint="/api/v5/trade/order",
                method="POST",
            )
    finally:
        release_read_only_observation_session_v1(handle)
