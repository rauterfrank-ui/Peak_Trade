"""Fail-closed ephemeral private-write gate for OKX EEA Demo XPerp campaign path."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlparse

from src.ops.section_11_12_8_okx_eea_demo_xperp_campaign_private_write_gate_v1.constants_v1 import (
    ACCEPTED_OWNER_GO_AUTHORIZATIONS,
    ACCEPTED_OWNER_GO_SCOPES,
    DEMO_MARKER_HEADER_NAME,
    DEMO_MARKER_HEADER_VALUE,
    ENVIRONMENT,
    INSTRUMENT_SCOPE_EXACT,
    INSTRUMENT_TYPE,
    LIVE_AUTHORIZED,
    MUTATION_ENDPOINTS,
    PACKAGE_DEFAULT_ORDER_POST_AUTHORIZED,
    REST_BASE,
    REST_HOST,
    RULE_TYPE,
    RUNTIME_MODE,
    SECTION_11_13_STARTED,
    VENUE,
)
from src.ops.section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1.constants_v1 import (
    ORDER_POST_AUTHORIZED as BINDING_PACKAGE_ORDER_POST_AUTHORIZED,
)


class OkxEeaDemoXperpCampaignPrivateWriteGateError(RuntimeError):
    """Fail-closed ephemeral write-gate violation."""


@dataclass(frozen=True)
class EphemeralCampaignPrivateWriteGateRecordV1:
    pass_gate: bool
    ephemeral_campaign_write_gate_pass: bool
    owner_go_scope: str
    venue: str
    rest_base: str
    instrument_scope_exact: str
    package_default_order_post_authorized: bool
    binding_package_order_post_authorized: bool
    live_authorized: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "pass_gate": self.pass_gate,
            "ephemeral_campaign_write_gate_pass": self.ephemeral_campaign_write_gate_pass,
            "owner_go_scope": self.owner_go_scope,
            "venue": self.venue,
            "rest_base": self.rest_base,
            "instrument_scope_exact": self.instrument_scope_exact,
            "package_default_order_post_authorized": (self.package_default_order_post_authorized),
            "binding_package_order_post_authorized": (self.binding_package_order_post_authorized),
            "live_authorized": self.live_authorized,
            "reason": self.reason,
        }


def _assert_host(rest_base: str) -> str:
    parsed = urlparse(str(rest_base or "").strip())
    host = (parsed.hostname or "").lower()
    if host != REST_HOST:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError(
            f"HOST_NOT_OKX_EEA_DEMO:{host or rest_base}"
        )
    if str(rest_base).rstrip("/") != REST_BASE:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError(f"REST_BASE_MISMATCH:{rest_base}")
    return host


def evaluate_ephemeral_campaign_private_write_gate_v1(
    *,
    owner_go_consumed: bool,
    owner_go_scope: str,
    owner_go_authorization: str,
    confirm_latched: bool,
    testnet_authorized_runtime: bool,
    campaign_enabled: bool,
    campaign_armed: bool,
    risk_gate_pass: bool,
    kill_switch_pass: bool,
    emergency_control_pass: bool,
    account_binding_pass: bool,
    endpoint_allowlist_pass: bool,
    bound_client_pass: bool,
    secretref_ephemeral_loaded: bool,
    venue: str = VENUE,
    environment: str = ENVIRONMENT,
    runtime_mode: str = RUNTIME_MODE,
    rest_base: str = REST_BASE,
    instrument_scope_exact: str = INSTRUMENT_SCOPE_EXACT,
    instrument_type: str = INSTRUMENT_TYPE,
    rule_type: str = RULE_TYPE,
    demo_marker_header_name: str = DEMO_MARKER_HEADER_NAME,
    demo_marker_header_value: str = DEMO_MARKER_HEADER_VALUE,
    headers: Mapping[str, str] | None = None,
    live_authorized: bool = False,
    live_mode: bool = False,
    package_default_order_post_authorized: bool = PACKAGE_DEFAULT_ORDER_POST_AUTHORIZED,
    binding_package_order_post_authorized: bool = BINDING_PACKAGE_ORDER_POST_AUTHORIZED,
    section_11_13_started: bool = SECTION_11_13_STARTED,
) -> EphemeralCampaignPrivateWriteGateRecordV1:
    """Default-deny ephemeral write gate. Raises on any unmet precondition."""
    if LIVE_AUTHORIZED is not False:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError("LIVE_AUTHORIZED_CONSTANT_DRIFT")
    if live_authorized or live_mode:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError("LIVE_PATH_HARD_BLOCK")
    if section_11_13_started or SECTION_11_13_STARTED:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError("SECTION_11_13_STARTED_HARD_BLOCK")
    if package_default_order_post_authorized is not False:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError(
            "PACKAGE_DEFAULT_ORDER_POST_MUST_REMAIN_FALSE"
        )
    if binding_package_order_post_authorized is not False:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError(
            "BINDING_PACKAGE_ORDER_POST_MUST_REMAIN_FALSE"
        )
    if not owner_go_consumed:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError("OWNER_GO_NOT_CONSUMED")
    scope = str(owner_go_scope or "").strip()
    authorization = str(owner_go_authorization or "").strip()
    if scope not in ACCEPTED_OWNER_GO_SCOPES:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError(f"OWNER_GO_SCOPE_MISMATCH:{scope}")
    if authorization not in ACCEPTED_OWNER_GO_AUTHORIZATIONS:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError(
            f"OWNER_GO_AUTHORIZATION_MISMATCH:{authorization}"
        )
    if not confirm_latched:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError("HIDDEN_CONFIRM_NOT_LATCHED")
    if not testnet_authorized_runtime:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError("TESTNET_RUNTIME_AUTH_REQUIRED")
    if not campaign_enabled or not campaign_armed:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError("CAMPAIGN_NOT_ENABLED_AND_ARMED")
    if not risk_gate_pass:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError("RISK_GATE_NOT_PASS")
    if not kill_switch_pass:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError("KILL_SWITCH_NOT_PASS")
    if not emergency_control_pass:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError("EMERGENCY_CONTROL_NOT_PASS")
    if not account_binding_pass:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError("ACCOUNT_BINDING_NOT_PASS")
    if not endpoint_allowlist_pass:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError("ENDPOINT_ALLOWLIST_NOT_PASS")
    if not bound_client_pass:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError("BOUND_CLIENT_NOT_PASS")
    if not secretref_ephemeral_loaded:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError("SECRETREF_EPHEMERAL_NOT_LOADED")
    if venue != VENUE:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError(f"VENUE_MISMATCH:{venue}")
    if environment != ENVIRONMENT:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError(f"ENVIRONMENT_MISMATCH:{environment}")
    if runtime_mode != RUNTIME_MODE:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError(f"RUNTIME_MODE_MISMATCH:{runtime_mode}")
    _assert_host(rest_base)
    if instrument_scope_exact != INSTRUMENT_SCOPE_EXACT:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError(
            f"INSTRUMENT_SCOPE_MISMATCH:{instrument_scope_exact}"
        )
    if instrument_type != INSTRUMENT_TYPE:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError(
            f"INSTRUMENT_TYPE_MISMATCH:{instrument_type}"
        )
    if rule_type != RULE_TYPE:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError(f"RULE_TYPE_MISMATCH:{rule_type}")
    if demo_marker_header_name != DEMO_MARKER_HEADER_NAME:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError("DEMO_MARKER_HEADER_NAME_MISMATCH")
    if str(demo_marker_header_value) != DEMO_MARKER_HEADER_VALUE:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError("DEMO_MARKER_HEADER_VALUE_MISMATCH")
    hdrs = {str(k).lower(): str(v) for k, v in dict(headers or {}).items()}
    if hdrs.get(DEMO_MARKER_HEADER_NAME) != DEMO_MARKER_HEADER_VALUE:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError("DEMO_MARKER_HEADER_MISSING")

    return EphemeralCampaignPrivateWriteGateRecordV1(
        pass_gate=True,
        ephemeral_campaign_write_gate_pass=True,
        owner_go_scope=scope,
        venue=VENUE,
        rest_base=REST_BASE,
        instrument_scope_exact=INSTRUMENT_SCOPE_EXACT,
        package_default_order_post_authorized=False,
        binding_package_order_post_authorized=False,
        live_authorized=False,
        reason="EPHEMERAL_XPERP_CAMPAIGN_PRIVATE_WRITE_GATE_PASS",
    )


def assert_mutation_allowed_under_ephemeral_gate_v1(
    *,
    endpoint: str,
    ephemeral_campaign_write_gate_pass: bool,
) -> None:
    """Allow mutation endpoints only when ephemeral gate explicitly passed."""
    path = str(endpoint or "").strip()
    if path not in MUTATION_ENDPOINTS:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError(
            f"ENDPOINT_NOT_MUTATION_ALLOWLIST:{path}"
        )
    if not ephemeral_campaign_write_gate_pass:
        raise OkxEeaDemoXperpCampaignPrivateWriteGateError(
            f"MUTATION_REQUIRES_EPHEMERAL_WRITE_GATE_PASS:{path}"
        )
