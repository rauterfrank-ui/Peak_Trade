"""Static + offline tests for bounded_futures_private_readonly_contract_v0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.bounded_futures_private_readonly_contract_v0 import (
    CONFIRM_TOKEN_PRIVATE_READONLY_REACHABILITY,
    DEMO_FUTURES_REST_BASE_URL,
    FUTURES_ORDER_MUTATION_ENDPOINTS,
    FUTURES_PRIVATE_READONLY_GET_ENDPOINTS,
    FUTURES_PRIVATE_API_AUTHORIZED,
    PACKAGE_MARKER,
    PRIVATE_READONLY_EXECUTE_AUTHORIZED_NOW,
    PRIVATE_READONLY_HTTP_WIRING_PRESENT,
    PRIVATE_READONLY_MODE,
    PRIVATE_READONLY_NETWORK_AUTHORIZED_NOW,
    build_private_readonly_checker_boundary,
    build_private_readonly_get_request_plan,
    build_private_readonly_http_request,
    build_private_readonly_plan_evidence_skeleton,
    evaluate_private_readonly_policy,
    summarize_private_response_for_evidence,
    validate_private_readonly_endpoint_path,
    validate_private_readonly_http_method,
    validate_private_readonly_rest_base_url,
    validate_private_readonly_url,
    validate_redacted_network_call_record,
)
from src.ops.bounded_futures_testnet_contract_v0 import (
    FUTURES_SESSION_AUTHORIZED_NOW,
    default_bounded_futures_private_readonly_reachability_v0_spec,
    evaluate_bounded_futures_testnet_evidence,
)
from src.ops.kraken_futures_demo_credential_presence_contract_v0 import (
    build_checker_boundary_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_MODULE = REPO_ROOT / "src" / "ops" / "bounded_futures_private_readonly_contract_v0.py"
HARNESS_SCRIPT = REPO_ROOT / "scripts" / "ops" / "archive_futures_testnet_harness_v0.py"

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_PRIVATE_READONLY_CONTRACT_GUARD_V0=true"


def test_package_marker_and_harness_wires_mode() -> None:
    assert TEST_PACKAGE_MARKER
    assert PACKAGE_MARKER in CONTRACT_MODULE.read_text(encoding="utf-8")
    assert PRIVATE_READONLY_HTTP_WIRING_PRESENT is True
    harness_text = HARNESS_SCRIPT.read_text(encoding="utf-8")
    assert PRIVATE_READONLY_MODE in harness_text
    assert "build_private_readonly_evidence_payload" in harness_text
    assert "SafePrivateReadonlyUrllibRestFetcher" in harness_text
    assert "run_private_readonly_reachability" in harness_text


def test_get_request_plan_has_three_endpoints() -> None:
    plan = build_private_readonly_get_request_plan()
    assert len(plan) == 3


def test_authority_flags_blocked() -> None:
    assert FUTURES_SESSION_AUTHORIZED_NOW is False
    assert FUTURES_PRIVATE_API_AUTHORIZED is False
    assert PRIVATE_READONLY_EXECUTE_AUTHORIZED_NOW is False
    assert PRIVATE_READONLY_NETWORK_AUTHORIZED_NOW is False


def test_allowlist_exactly_three_get_endpoints() -> None:
    assert FUTURES_PRIVATE_READONLY_GET_ENDPOINTS == frozenset(
        {
            "/derivatives/api/v3/accounts",
            "/derivatives/api/v3/openpositions",
            "/derivatives/api/v3/openorders",
        }
    )


def test_order_mutation_endpoints_blocked_by_policy() -> None:
    policy = evaluate_private_readonly_policy(
        endpoints_called=list(FUTURES_ORDER_MUTATION_ENDPOINTS),
        http_methods=["POST"],
    )
    assert policy["private_readonly_policy_pass"] is False
    assert policy["order_endpoints_blocked"] is False


def test_post_http_method_blocked() -> None:
    assert validate_private_readonly_http_method("POST") != []


def test_live_host_blocked() -> None:
    reasons = validate_private_readonly_rest_base_url(
        "https://futures.kraken.com/derivatives/api/v3"
    )
    assert reasons


def test_demo_host_allowed() -> None:
    assert validate_private_readonly_rest_base_url(DEMO_FUTURES_REST_BASE_URL) == []


def test_sendorder_url_rejected() -> None:
    url = f"{DEMO_FUTURES_REST_BASE_URL}/sendorder"
    assert validate_private_readonly_url(url, rest_base_url=DEMO_FUTURES_REST_BASE_URL)


def test_accounts_openpositions_openorders_paths_allowed() -> None:
    for ep in FUTURES_PRIVATE_READONLY_GET_ENDPOINTS:
        assert validate_private_readonly_endpoint_path(ep) == []


def test_redaction_contract_no_raw_body() -> None:
    body = json.dumps(
        {
            "accounts": [{"type": "marginAccount"}],
            "openPositions": [],
        }
    ).encode()
    record = summarize_private_response_for_evidence(
        endpoint="/derivatives/api/v3/accounts",
        http_status=200,
        body=body,
    )
    assert record["response_redacted"] is True
    assert "response_body" not in record
    assert validate_redacted_network_call_record(record) == []


def test_redaction_fails_if_raw_values_emitted_flag_set() -> None:
    bad = {
        "endpoint": "/derivatives/api/v3/openorders",
        "http_method": "GET",
        "http_status": 200,
        "http_status_class": "2xx",
        "response_size_bytes": 1,
        "response_sha256": "a" * 64,
        "response_redacted": True,
        "parsed_summary": {"raw_values_emitted": True},
        "auth_header_names": [],
        "credential_values_logged": False,
    }
    assert validate_redacted_network_call_record(bad)


def test_credential_presence_does_not_authorize_execute() -> None:
    boundary = build_private_readonly_checker_boundary()
    presence = build_checker_boundary_v0()
    assert boundary["futures_private_api_authorized"] is False
    assert boundary["next_execute_allowed"] is False
    assert boundary["credential_presence_implies_execute"] is False
    assert presence["futures_private_api_authorized"] is False


def test_plan_skeleton_passes_pe8_private_readonly_spec() -> None:
    evidence = build_private_readonly_plan_evidence_skeleton(run_id="offline")
    spec = default_bounded_futures_private_readonly_reachability_v0_spec()
    result = evaluate_bounded_futures_testnet_evidence(evidence, spec=spec)
    assert result["bounded_futures_testnet_pass"] is True


def test_confirm_token_reserved_not_empty() -> None:
    assert "PRIVATE_READONLY" in CONFIRM_TOKEN_PRIVATE_READONLY_REACHABILITY
