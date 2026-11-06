"""Threat-model delta for OKX Global Demo shared-host binding (V2.1 §4.3/§20)."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_12_8_okx_global_demo_venue_host_account_instrument_binding_v1.constants_v1 import (
    CREDENTIAL_CLASS,
    CYBERSECURITY_RUNBOOK_BINDINGS,
    DEMO_MARKER_HEADER_NAME,
    DEMO_MARKER_HEADER_VALUE,
    INSTRUMENT_SCOPE_EXACT,
    REST_HOST,
    THREAT_MODEL_DELTA_ID,
    VENUE,
)


def build_threat_model_delta_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "THREAT_MODEL_DELTA_V1",
        "THREAT_MODEL_DELTA_ID": THREAT_MODEL_DELTA_ID,
        "CYBERSECURITY_RUNBOOK_BINDINGS": list(CYBERSECURITY_RUNBOOK_BINDINGS),
        "TRIGGER": "NEW_VENUE_SCOPE_OKX_GLOBAL_DEMO_FOR_SECTION_11_12_8",
        "VENUE": VENUE,
        "REST_HOST": REST_HOST,
        "SHARED_HOST_WITH_LIVE": True,
        "NEW_THREATS": [
            "HOST_ENDPOINT_SUBSTITUTION_VIA_MISSING_DEMO_HEADER",
            "CREDENTIAL_CROSS_USE_LIVE_OR_EEA_KEYS_ON_SHARED_HOST",
            "INSTRUMENT_SUBSTITUTION_AWAY_FROM_BTC_USDT_SWAP",
            "SILENT_FALLBACK_TO_OKX_EEA_OR_LIVE",
            "AUTHORITY_ESCALATION_FROM_BINDING_PACKAGE_TO_ORDER_POST",
        ],
        "COMPENSATING_CONTROLS": [
            {
                "control": "MANDATORY_DEMO_MARKER_HEADER",
                "header": f"{DEMO_MARKER_HEADER_NAME}:{DEMO_MARKER_HEADER_VALUE}",
                "fail_closed_on_absence": True,
            },
            {
                "control": "MANDATORY_DEMO_CREDENTIAL_CLASS",
                "credential_class": CREDENTIAL_CLASS,
                "live_and_eea_classes_hard_blocked": True,
            },
            {
                "control": "EXACT_INSTRUMENT_SCOPE",
                "instrument": INSTRUMENT_SCOPE_EXACT,
                "generic_substitution_forbidden": True,
            },
            {
                "control": "SECRETREF_ONLY_CREDENTIAL_PATH",
                "plaintext_forbidden": True,
            },
            {
                "control": "ORDER_POST_HARD_BLOCK_IN_BINDING_PACKAGE",
                "order_post_authorized": False,
            },
            {
                "control": "NO_SILENT_HOST_VENUE_INSTRUMENT_FALLBACK",
                "fail_closed_on_ambiguity": True,
            },
        ],
        "PRE_LIVE_CYBERSECURITY_GATE_EFFECT": "NONE_REMAINS_NOT_PASSED",
        "LIVE_AUTHORIZED_EFFECT": "NONE_REMAINS_FALSE",
        "SECTION_11_13_EFFECT": "NONE_REMAINS_UNSTARTED",
        "ok": True,
    }
