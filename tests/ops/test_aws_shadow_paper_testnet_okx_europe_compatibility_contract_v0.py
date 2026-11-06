"""Offline tests for AWS Shadow/Paper/Testnet OKX-Europe compatibility contract (v0).

Class-4 scoped: no network, AWS calls, credentials, runtime, or deployment.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.ops.aws_shadow_paper_testnet_okx_europe_compatibility_contract_v0 import (
    AUTHORITY_IMPACT,
    AUTOMATIC_INSTRUMENT_SUBSTITUTION_ALLOWED,
    AWS_RUNTIME_OWNER_PATHS,
    AwsShadowPaperTestnetCompatibilityError,
    AwsShadowPaperTestnetCompatibilityVerdictKind,
    BoundedReconnectPolicy,
    CredentialSlotBinding,
    DEFAULT_PRIVATE_WS_HOST,
    FORBIDDEN_SERIALIZATION_KEYS,
    PACKAGE_MARKER,
    REASON_AUTOMATIC_INSTRUMENT_SUBSTITUTION,
    REASON_AUTOMATIC_PRODUCTION_FALLBACK,
    REASON_AWS_DEPLOYMENT_AUTHORIZED,
    REASON_AWS_RUNTIME_EXECUTED,
    REASON_CREDENTIALS_NOT_EXTERNALIZED,
    REASON_CREDENTIAL_SCOPES_NOT_SEPARATED,
    REASON_DEMO_PRODUCTION_INSTRUMENT_COLLISION,
    REASON_HARDCODED_CREDENTIALS,
    REASON_LOCAL_FILE_PATH_DEPENDENCY,
    REASON_LOCALHOST_DEPENDENCY,
    REASON_LOG_CREDENTIALS,
    REASON_PRODUCTION_INSTRUMENT_IN_NON_PRODUCTION_ENV,
    REASON_PUBLIC_WS_HOST_MISMATCH,
    REASON_RATE_LIMIT_NOT_FAIL_CLOSED,
    REASON_RECONNECT_POLICY_MISSING,
    REASON_REST_HOST_MISMATCH,
    REASON_REST_HOST_PRODUCTION,
    REASON_RUNTIME_ENVIRONMENT_FORBIDDEN,
    REASON_SECRET_MATERIAL_REJECTED,
    REASON_SHARED_READONLY_TRADE_SECRET_SLOT,
    REASON_SIMULATION_HEADER_DISABLED,
    REASON_SIMULATION_HEADER_NAME_MISMATCH,
    REASON_UNBOUNDED_RECONNECT,
    REASON_UNBOUNDED_RETRY,
    REASON_WEBSOCKET_PORT_443_ASSUMED,
    REASON_WEBSOCKET_PORT_NOT_EXPLICIT,
    REQUIRED_DEMO_PUBLIC_WS_HOST,
    REQUIRED_REST_HOST,
    REQUIRED_WEBSOCKET_PORT,
    SIMULATION_HEADER_NAME,
    SIMULATION_HEADER_VALUE,
    default_aws_shadow_paper_testnet_okx_europe_binding_input,
    default_bounded_reconnect_policy,
    default_okx_europe_credential_slots,
    default_valid_aws_shadow_paper_testnet_okx_europe_binding_input,
    evaluate_aws_shadow_paper_testnet_okx_europe_compatibility,
    build_aws_shadow_paper_testnet_closeout_machine_lines,
    reject_secret_like_mapping,
    serialize_aws_shadow_paper_testnet_closeout_machine_lines,
    serialize_aws_shadow_paper_testnet_okx_europe_compatibility_result,
    validate_aws_shadow_paper_testnet_okx_europe_compatibility_result,
)
from src.ops.bounded_futures_testnet_venue_binding_v0 import (
    DEMO_REFERENCE_INSTRUMENT_ID,
    PRODUCTION_INSTRUMENT_ID,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_MODULE = (
    REPO_ROOT / "src" / "ops" / "aws_shadow_paper_testnet_okx_europe_compatibility_contract_v0.py"
)
VENUE_BINDING_MODULE = REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_venue_binding_v0.py"

TEST_PACKAGE_MARKER = "AWS_SHADOW_PAPER_TESTNET_OKX_EUROPE_COMPATIBILITY_CONTRACT_V0_TEST=true"
OPERATOR_GO_BINDING = (
    "GO_PACKAGE_E_E2_INV033_OKX_EUROPE_AWS_COMPATIBILITY_WIP_RECOVERY_COMMIT_AND_PUSH_V0"
)


def test_package_marker_present() -> None:
    assert TEST_PACKAGE_MARKER
    assert OPERATOR_GO_BINDING
    assert PACKAGE_MARKER in CONTRACT_MODULE.read_text(encoding="utf-8")


def test_default_input_fail_closed() -> None:
    result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_aws_shadow_paper_testnet_okx_europe_binding_input()
    )
    assert result.verdict == AwsShadowPaperTestnetCompatibilityVerdictKind.FAIL_CLOSED
    assert result.aws_runtime_compatible is False
    assert result.aws_deployment_authorized is False
    assert result.automatic_production_fallback_allowed is False
    assert result.automatic_instrument_substitution_allowed is False
    validate_aws_shadow_paper_testnet_okx_europe_compatibility_result(result)


def test_valid_binding_aws_runtime_compatible() -> None:
    result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(runtime_environment="paper")
    )
    assert result.verdict == AwsShadowPaperTestnetCompatibilityVerdictKind.AWS_RUNTIME_COMPATIBLE
    assert result.aws_runtime_compatible is True
    assert result.runtime_environment_explicit is True
    assert result.rest_host_explicit is True
    assert result.public_ws_host_explicit is True
    assert result.private_ws_host_explicit is True
    assert result.websocket_port_explicit is True
    assert result.simulation_header_explicit is True
    assert result.credentials_externalized is True
    assert result.credential_scopes_separated is True
    assert result.secrets_log_redaction_required is True
    assert result.stateless_restart_supported is True
    assert result.durable_reconciliation_supported is True
    assert result.bounded_reconnect_policy_required is True
    assert result.rate_limit_fail_closed is True
    assert result.production_demo_environment_separation is True
    assert result.automatic_production_fallback_allowed is False
    assert result.automatic_instrument_substitution_allowed is False
    assert result.aws_deployment_authorized is False
    validate_aws_shadow_paper_testnet_okx_europe_compatibility_result(result)


@pytest.mark.parametrize("runtime_environment", ["shadow", "paper", "testnet"])
def test_allowed_runtime_environments(runtime_environment: str) -> None:
    result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(
            runtime_environment=runtime_environment
        )
    )
    assert result.verdict == AwsShadowPaperTestnetCompatibilityVerdictKind.AWS_RUNTIME_COMPATIBLE


@pytest.mark.parametrize("runtime_environment", ["live", "production", "mainnet", ""])
def test_forbidden_runtime_environments(runtime_environment: str) -> None:
    result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(
            runtime_environment=runtime_environment
        )
    )
    assert result.verdict == AwsShadowPaperTestnetCompatibilityVerdictKind.FAIL_CLOSED
    assert REASON_RUNTIME_ENVIRONMENT_FORBIDDEN in result.reason_codes or not runtime_environment


def test_rest_host_explicit_eea_okx() -> None:
    result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input()
    )
    assert result.rest_host_explicit is True
    assert REQUIRED_REST_HOST == "https://eea.okx.com"
    bad = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(
            rest_host="https://www.okx.com"
        )
    )
    assert (
        REASON_REST_HOST_MISMATCH in bad.reason_codes
        or REASON_REST_HOST_PRODUCTION in bad.reason_codes
    )


def test_public_ws_host_explicit_demo_endpoint() -> None:
    result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input()
    )
    assert result.public_ws_host_explicit is True
    assert REQUIRED_DEMO_PUBLIC_WS_HOST == "wss://wseeapap.okx.com:8443/ws/v5/public"
    bad = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(
            public_ws_host="wss://ws.okx.com:443/ws/v5/public"
        )
    )
    assert REASON_PUBLIC_WS_HOST_MISMATCH in bad.reason_codes


def test_private_ws_host_explicit_demo_endpoint() -> None:
    result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input()
    )
    assert result.private_ws_host_explicit is True
    assert DEFAULT_PRIVATE_WS_HOST.endswith(":8443/ws/v5/private")


def test_websocket_port_8443_explicit_not_443() -> None:
    result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input()
    )
    assert result.websocket_port_explicit is True
    implicit_443 = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(
            public_ws_host="wss://wseeapap.okx.com/ws/v5/public",
            websocket_port=443,
        )
    )
    assert (
        REASON_WEBSOCKET_PORT_NOT_EXPLICIT in implicit_443.reason_codes
        or REASON_WEBSOCKET_PORT_443_ASSUMED in implicit_443.reason_codes
        or REASON_PUBLIC_WS_HOST_MISMATCH in implicit_443.reason_codes
    )
    assert REQUIRED_WEBSOCKET_PORT == 8443


def test_simulation_header_explicit_and_environment_specific() -> None:
    result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input()
    )
    assert result.simulation_header_explicit is True
    disabled = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(
            simulation_header_enabled=False
        )
    )
    assert REASON_SIMULATION_HEADER_DISABLED in disabled.reason_codes
    wrong_name = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(
            simulation_header_name="x-demo-trading"
        )
    )
    assert REASON_SIMULATION_HEADER_NAME_MISMATCH in wrong_name.reason_codes
    assert SIMULATION_HEADER_NAME == "x-simulated-trading"
    assert SIMULATION_HEADER_VALUE == "1"


def test_credential_scopes_separated() -> None:
    slots = default_okx_europe_credential_slots()
    assert {slot.slot_id for slot in slots} == {"public", "readonly_private", "trade"}
    result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input()
    )
    assert result.credential_scopes_separated is True
    shared = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(
            shared_readonly_trade_secret_slot=True
        )
    )
    assert REASON_SHARED_READONLY_TRADE_SECRET_SLOT in shared.reason_codes
    hardcoded = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(hardcoded_credentials=True)
    )
    assert REASON_HARDCODED_CREDENTIALS in hardcoded.reason_codes


def test_credentials_externalized_via_env_slots() -> None:
    result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input()
    )
    assert result.credentials_externalized is True
    missing = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(credential_slots=())
    )
    assert REASON_CREDENTIALS_NOT_EXTERNALIZED in missing.reason_codes
    assert REASON_CREDENTIAL_SCOPES_NOT_SEPARATED in missing.reason_codes


def test_secret_redaction_invariants() -> None:
    result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input()
    )
    data = serialize_aws_shadow_paper_testnet_okx_europe_compatibility_result(result)
    assert data["secrets_log_redaction_required"] is True
    assert data["value_redacted"] is True
    assert data["no_secret_material"] is True
    for key in data:
        assert key.lower() not in FORBIDDEN_SERIALIZATION_KEYS
    logged = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(log_credentials=True)
    )
    assert REASON_LOG_CREDENTIALS in logged.reason_codes
    secret_reasons = reject_secret_like_mapping({"api_secret": "redacted"})
    assert REASON_SECRET_MATERIAL_REJECTED in secret_reasons


def test_no_localhost_or_local_file_dependencies() -> None:
    local_path = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(
            local_file_path_dependencies=("/tmp/secrets.env",)
        )
    )
    assert REASON_LOCAL_FILE_PATH_DEPENDENCY in local_path.reason_codes
    localhost = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(
            localhost_dependencies=("127.0.0.1",)
        )
    )
    assert REASON_LOCALHOST_DEPENDENCY in localhost.reason_codes


def test_bounded_reconnect_policy_required() -> None:
    result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input()
    )
    assert result.bounded_reconnect_policy_required is True
    missing = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(reconnect_policy=None)
    )
    assert REASON_RECONNECT_POLICY_MISSING in missing.reason_codes
    unbounded = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(unbounded_reconnect=True)
    )
    assert REASON_UNBOUNDED_RECONNECT in unbounded.reason_codes
    retry = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(unbounded_retry=True)
    )
    assert REASON_UNBOUNDED_RETRY in retry.reason_codes


def test_rate_limit_fail_closed() -> None:
    result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input()
    )
    assert result.rate_limit_fail_closed is True
    open_limit = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(
            rate_limit_fail_closed=False
        )
    )
    assert REASON_RATE_LIMIT_NOT_FAIL_CLOSED in open_limit.reason_codes


def test_production_demo_instrument_separation_eth_xperp() -> None:
    result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input()
    )
    assert result.production_demo_environment_separation is True
    assert PRODUCTION_INSTRUMENT_ID == "ETH-USD_UM_XPERP-310404"
    assert DEMO_REFERENCE_INSTRUMENT_ID == "ETH-USD_UM_XPERP-310328"
    collision = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(
            demo_instrument_id=PRODUCTION_INSTRUMENT_ID,
            production_instrument_id=PRODUCTION_INSTRUMENT_ID,
        )
    )
    assert REASON_DEMO_PRODUCTION_INSTRUMENT_COLLISION in collision.reason_codes
    prod_active = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(
            active_instrument_id=PRODUCTION_INSTRUMENT_ID
        )
    )
    assert REASON_PRODUCTION_INSTRUMENT_IN_NON_PRODUCTION_ENV in prod_active.reason_codes


def test_automatic_instrument_substitution_rejected() -> None:
    assert AUTOMATIC_INSTRUMENT_SUBSTITUTION_ALLOWED is False
    result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(
            automatic_instrument_substitution=True
        )
    )
    assert REASON_AUTOMATIC_INSTRUMENT_SUBSTITUTION in result.reason_codes


def test_no_automatic_production_fallback() -> None:
    result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input()
    )
    assert result.automatic_production_fallback_allowed is False
    fallback = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(
            automatic_production_fallback=True
        )
    )
    assert REASON_AUTOMATIC_PRODUCTION_FALLBACK in fallback.reason_codes


def test_aws_deployment_and_runtime_not_authorized() -> None:
    result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input()
    )
    assert result.aws_deployment_authorized is False
    deploy = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(
            aws_deployment_authorized=True
        )
    )
    assert REASON_AWS_DEPLOYMENT_AUTHORIZED in deploy.reason_codes
    executed = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(aws_runtime_executed=True)
    )
    assert REASON_AWS_RUNTIME_EXECUTED in executed.reason_codes


def test_closeout_machine_lines_required_fields() -> None:
    result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input()
    )
    closeout = build_aws_shadow_paper_testnet_closeout_machine_lines(result)
    serialized = serialize_aws_shadow_paper_testnet_closeout_machine_lines(closeout)
    assert serialized["AWS_RUNTIME_COMPATIBLE"] == "true"
    assert serialized["AWS_DEPLOYMENT_AUTHORIZED"] == "false"
    assert serialized["AWS_RUNTIME_EXECUTED"] == "false"
    assert serialized["AWS_WEBSOCKET_PORT_REQUIREMENT"] == REQUIRED_WEBSOCKET_PORT
    assert closeout.aws_deployment_authorized is False
    assert closeout.aws_runtime_executed is False


def test_aws_runtime_owner_paths_exist_and_reference_venue_binding() -> None:
    assert "src/ops/bounded_futures_testnet_venue_binding_v0.py" in AWS_RUNTIME_OWNER_PATHS
    for rel_path in AWS_RUNTIME_OWNER_PATHS:
        assert (REPO_ROOT / rel_path).is_file(), rel_path
    assert VENUE_BINDING_MODULE.is_file()


def test_serialized_result_includes_closeout_machine_lines() -> None:
    result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input()
    )
    data = serialize_aws_shadow_paper_testnet_okx_europe_compatibility_result(result)
    closeout = data["closeout_machine_lines"]
    required = {
        "AWS_RUNTIME_COMPATIBLE",
        "AWS_RUNTIME_OWNER_PATHS",
        "AWS_CONFIG_REUSE_POSSIBLE",
        "AWS_SECRET_INJECTION_COMPATIBLE",
        "AWS_NETWORK_REQUIREMENTS_DOCUMENTED",
        "AWS_WEBSOCKET_PORT_REQUIREMENT",
        "AWS_SIMULATION_HEADER_TRANSPORTABLE",
        "AWS_RESTART_RECONCILIATION_COMPATIBLE",
        "AWS_PRODUCTION_DEMO_SEPARATION_PROVEN",
        "AWS_DEPLOYMENT_AUTHORIZED",
        "AWS_RUNTIME_EXECUTED",
    }
    assert required.issubset(closeout.keys())


def test_authority_impact_always_no_authority_change() -> None:
    default_result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_aws_shadow_paper_testnet_okx_europe_binding_input()
    )
    ok_result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input()
    )
    assert default_result.authority_impact == AUTHORITY_IMPACT
    assert ok_result.authority_impact == AUTHORITY_IMPACT


def test_deterministic_output_same_input() -> None:
    inp = default_valid_aws_shadow_paper_testnet_okx_europe_binding_input()
    first = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(inp)
    second = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(inp)
    assert first == second


def test_validate_result_raises_on_tampered_deployment_authorization() -> None:
    ok = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input()
    )
    bad = type(ok)(
        verdict=ok.verdict,
        reason_codes=ok.reason_codes,
        aws_runtime_compatible=ok.aws_runtime_compatible,
        runtime_environment_explicit=ok.runtime_environment_explicit,
        rest_host_explicit=ok.rest_host_explicit,
        public_ws_host_explicit=ok.public_ws_host_explicit,
        private_ws_host_explicit=ok.private_ws_host_explicit,
        websocket_port_explicit=ok.websocket_port_explicit,
        simulation_header_explicit=ok.simulation_header_explicit,
        credentials_externalized=ok.credentials_externalized,
        credential_scopes_separated=ok.credential_scopes_separated,
        secrets_log_redaction_required=ok.secrets_log_redaction_required,
        stateless_restart_supported=ok.stateless_restart_supported,
        durable_reconciliation_supported=ok.durable_reconciliation_supported,
        bounded_reconnect_policy_required=ok.bounded_reconnect_policy_required,
        rate_limit_fail_closed=ok.rate_limit_fail_closed,
        production_demo_environment_separation=ok.production_demo_environment_separation,
        automatic_production_fallback_allowed=ok.automatic_production_fallback_allowed,
        automatic_instrument_substitution_allowed=ok.automatic_instrument_substitution_allowed,
        aws_deployment_authorized=True,
        authority_impact=ok.authority_impact,
        value_redacted=ok.value_redacted,
        no_secret_material=ok.no_secret_material,
    )
    with pytest.raises(AwsShadowPaperTestnetCompatibilityError):
        validate_aws_shadow_paper_testnet_okx_europe_compatibility_result(bad)


def test_no_execution_risk_layer_imports() -> None:
    tree = ast.parse(CONTRACT_MODULE.read_text(encoding="utf-8"))
    forbidden_modules = ("boto3", "requests", "urllib.request", "socket", "subprocess")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("src.execution")
                assert not alias.name.startswith("src.risk_layer")
                assert alias.name not in forbidden_modules
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("src.execution")
            assert not node.module.startswith("src.risk_layer")
            assert node.module not in forbidden_modules


def test_shared_env_var_for_readonly_and_trade_rejected() -> None:
    slots = (
        CredentialSlotBinding(
            slot_id="public",
            env_var_name="OKX_EEA_PUBLIC_API_KEY",
            capability="public_read",
        ),
        CredentialSlotBinding(
            slot_id="readonly_private",
            env_var_name="OKX_EEA_SHARED_KEY",
            capability="private_readonly",
        ),
        CredentialSlotBinding(
            slot_id="trade",
            env_var_name="OKX_EEA_SHARED_KEY",
            capability="trade",
        ),
    )
    result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(credential_slots=slots)
    )
    assert REASON_CREDENTIAL_SCOPES_NOT_SEPARATED in result.reason_codes


def test_invalid_reconnect_policy_fail_closed() -> None:
    bad_policy = BoundedReconnectPolicy(
        max_attempts=0,
        initial_backoff_seconds=1.0,
        max_backoff_seconds=30.0,
        heartbeat_interval_seconds=20.0,
        reconnect_timeout_seconds=10.0,
    )
    result = evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
        default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(reconnect_policy=bad_policy)
    )
    assert REASON_UNBOUNDED_RECONNECT in result.reason_codes
