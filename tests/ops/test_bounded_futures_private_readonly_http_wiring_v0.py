"""Offline tests for private-readonly HTTP wiring (mocked fetcher only)."""

from __future__ import annotations

import base64
import json

import pytest

from scripts.ops import archive_futures_testnet_harness_v0 as harness
from src.ops.bounded_futures_private_readonly_contract_v0 import (
    CONFIRM_TOKEN_PRIVATE_READONLY_REACHABILITY,
    DEMO_FUTURES_REST_BASE_URL,
    FUTURES_PRIVATE_READONLY_GET_ENDPOINTS,
    PRIVATE_READONLY_ENDPOINT_ORDER,
    PRIVATE_READONLY_HTTP_WIRING_PRESENT,
    PrivateReadonlyHttpRequest,
    build_private_readonly_get_request_plan,
    build_private_readonly_http_request,
    build_private_readonly_plan_evidence_skeleton,
    resolve_private_readonly_credentials_from_environ,
    run_private_readonly_reachability,
    summarize_private_response_for_evidence,
    validate_redacted_network_call_record,
)
from src.ops.kraken_futures_demo_credential_presence_contract_v0 import (
    build_checker_boundary_v0,
)

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_PRIVATE_READONLY_HTTP_WIRING_GUARD_V0=true"


class _FakePrivateFetcher:
    def __init__(self, *, body: bytes | None = None) -> None:
        self.requests: list[PrivateReadonlyHttpRequest] = []
        self._body = body if body is not None else b'{"accounts":[]}'

    def fetch(
        self,
        http_request: PrivateReadonlyHttpRequest,
        *,
        timeout_seconds: float,
    ) -> tuple[int, bytes]:
        self.requests.append(http_request)
        assert http_request.method == "GET"
        assert "sendorder" not in http_request.url
        assert set(http_request.headers.keys()) == {"APIKey", "Authent", "Nonce"}
        return 200, self._body


def test_package_marker_and_http_wiring_flag() -> None:
    assert TEST_PACKAGE_MARKER
    assert PRIVATE_READONLY_HTTP_WIRING_PRESENT is True
    assert harness.SAFE_PRIVATE_READONLY_URLLIB_FETCHER_PRESENT is True


def test_request_plan_builds_exactly_three_gets() -> None:
    plan = build_private_readonly_get_request_plan()
    assert len(plan) == 3
    assert [row["method"] for row in plan] == ["GET", "GET", "GET"]
    assert {row["endpoint_path"] for row in plan} == set(FUTURES_PRIVATE_READONLY_GET_ENDPOINTS)
    assert list(PRIVATE_READONLY_ENDPOINT_ORDER) == [
        "/derivatives/api/v3/accounts",
        "/derivatives/api/v3/openpositions",
        "/derivatives/api/v3/openorders",
    ]


def test_blocklisted_endpoint_cannot_be_built() -> None:
    secret = base64.b64encode(b"test-secret-bytes-32chars-long!!").decode()
    with pytest.raises(ValueError, match="forbidden|not allowed|allowlist"):
        build_private_readonly_http_request(
            rest_base_url=DEMO_FUTURES_REST_BASE_URL,
            endpoint_path="/derivatives/api/v3/sendorder",
            api_key="demo-key",
            api_secret_b64=secret,
        )


def test_auth_header_names_present_values_not_in_evidence() -> None:
    secret = base64.b64encode(b"test-secret-bytes-32chars-long!!").decode()
    http_request = build_private_readonly_http_request(
        rest_base_url=DEMO_FUTURES_REST_BASE_URL,
        endpoint_path="/derivatives/api/v3/accounts",
        api_key="demo-key-not-logged",
        api_secret_b64=secret,
        nonce="12345",
    )
    assert http_request.auth_header_names == ("APIKey", "Authent", "Nonce")
    record = summarize_private_response_for_evidence(
        endpoint=http_request.endpoint_path,
        http_status=200,
        body=b'{"accounts":[{"balance":"999"}],"openPositions":[]}',
        auth_header_names=http_request.auth_header_names,
    )
    assert record["credential_values_logged"] is False
    assert "999" not in json.dumps(record)
    assert "demo-key" not in json.dumps(record)
    assert validate_redacted_network_call_record(record) == []


def test_mocked_reachability_calls_three_endpoints() -> None:
    secret = base64.b64encode(b"test-secret-bytes-32chars-long!!").decode()
    fetcher = _FakePrivateFetcher()
    result = run_private_readonly_reachability(
        rest_base_url=DEMO_FUTURES_REST_BASE_URL,
        api_key="demo-key",
        api_secret_b64=secret,
        fetcher=fetcher,
        duration_cap_seconds=60,
    )
    assert result.request_count == 3
    assert set(result.endpoints_called) == set(FUTURES_PRIVATE_READONLY_GET_ENDPOINTS)
    assert result.private_readonly_reachability_proven is True
    assert len(fetcher.requests) == 3


def test_credentials_present_does_not_authorize_execute() -> None:
    boundary = build_checker_boundary_v0()
    skeleton = build_private_readonly_plan_evidence_skeleton(run_id="x")
    assert boundary["futures_private_api_authorized"] is False
    assert skeleton["futures_private_api_authorized"] is False
    assert skeleton["private_readonly_execute_wired"] is True


def test_resolve_credentials_from_environ_without_logging() -> None:
    secret = base64.b64encode(b"s" * 32).decode()
    creds = resolve_private_readonly_credentials_from_environ(
        {
            "KRAKEN_FUTURES_DEMO_API_KEY": "k",
            "KRAKEN_FUTURES_DEMO_API_SECRET": secret,
        }
    )
    assert creds == ("k", secret)


def test_harness_private_execute_blocked_without_confirm(tmp_path) -> None:
    from tests.ops.test_archive_futures_testnet_harness_v0 import _durable_test_archive_root

    archive = _durable_test_archive_root(tmp_path)
    rc = harness.main(
        [
            "--archive-root",
            str(archive),
            "--run-id",
            "no-confirm",
            "--mode",
            "private_readonly_reachability_only",
            "--execute-network",
        ],
        environ={
            "KRAKEN_FUTURES_DEMO_API_KEY": "k",
            "KRAKEN_FUTURES_DEMO_API_SECRET": base64.b64encode(b"x" * 32).decode(),
        },
    )
    assert rc == harness.USAGE_EXIT


def test_harness_private_execute_mocked_fetcher(tmp_path) -> None:
    from tests.ops.test_archive_futures_testnet_harness_v0 import _durable_test_archive_root

    archive = _durable_test_archive_root(tmp_path)
    fake = _FakePrivateFetcher()
    secret = base64.b64encode(b"test-secret-bytes-32chars-long!!").decode()
    rc = harness.main(
        [
            "--archive-root",
            str(archive),
            "--run-id",
            "privexec",
            "--mode",
            "private_readonly_reachability_only",
            "--execute-network",
            "--confirm-futures-private-readonly-reachability",
            CONFIRM_TOKEN_PRIVATE_READONLY_REACHABILITY,
        ],
        private_fetcher=fake,
        environ={
            "KRAKEN_FUTURES_DEMO_API_KEY": "demo-key",
            "KRAKEN_FUTURES_DEMO_API_SECRET": secret,
        },
    )
    assert rc == 0
    assert len(fake.requests) == 3
    evidence_path = list((archive / "runtime").iterdir())[0] / "FUTURES_EVIDENCE.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["request_count"] == 3
    assert evidence["private_readonly_reachability_proven"] is True
    dump = json.dumps(evidence)
    assert "demo-key" not in dump
    assert evidence["futures_private_api_authorized"] is False
