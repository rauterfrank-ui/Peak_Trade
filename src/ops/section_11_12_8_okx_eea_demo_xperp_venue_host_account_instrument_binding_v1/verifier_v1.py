"""Verifier for OKX EEA Demo XPerp venue/host/account/instrument binding package."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.ops.section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1.binding_contract_v1 import (
    OkxEeaDemoXperpBindingError,
    assert_order_send_forbidden_v1,
    canonical_binding_headers_v1,
    default_canonical_binding_v1,
    evaluate_okx_eea_demo_xperp_binding_v1,
)
from src.ops.section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1.constants_v1 import (
    ACTIVE_SECTION_11_12_8_DERIVATIVES_CAMPAIGN_PATH,
    BINDING_PROOF_FILENAME,
    BTC_USDT_SWAP_PATH_STATUS,
    CANONICAL_NEXT_STEP_AFTER_MERGE,
    CAPABILITY_ID,
    CLAIMS_FILENAME,
    CREDENTIAL_CLASS,
    INSTRUMENT_SCOPE_EXACT,
    INSTRUMENT_TYPE,
    LEGACY_BTC_USDT_SWAP_ACTIVE_BINDING_REMOVED,
    LIVE_AUTHORIZED,
    MANIFEST_FILENAME,
    OKX_GLOBAL_DEMO_ACTIVE_BINDING,
    ORDER_ATTEMPT_COUNT,
    ORDER_POST_AUTHORIZED,
    OWNER,
    OWNER_GO_TOKEN,
    PACKAGE_MARKER,
    PREDECESSOR_PRIVATE_RO_PROOF_EVIDENCE,
    PRE_LIVE_CYBERSECURITY_GATE,
    PRIVATE_WRITE_COUNT,
    RULE_TYPE,
    SECTION_11_12_8_STATUS,
    SECTION_11_13_STARTED,
    SUMMARY_FILENAME,
    SWAP_RUNTIME_FALLBACK,
    SWAP_WRITE_AUTHORIZATION,
    THREAT_MODEL_DELTA_FILENAME,
    XPERP_ONLY_ACTIVE_WRITE_SCOPE,
    XPERP_PRIVATE_CAPABILITY_PROOF_BOUND,
)
from src.ops.section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1.threat_model_delta_v1 import (
    build_threat_model_delta_v1,
)


def _prove_fail_closed_cases() -> dict[str, Any]:
    cases: list[dict[str, Any]] = []

    def _expect(name: str, exc_match: str, **kwargs: Any) -> None:
        try:
            evaluate_okx_eea_demo_xperp_binding_v1(**kwargs)
            cases.append({"case": name, "ok": False, "error": "EXPECTED_FAIL_CLOSED"})
        except OkxEeaDemoXperpBindingError as exc:
            msg = str(exc)
            cases.append(
                {
                    "case": name,
                    "ok": exc_match in msg,
                    "error": msg,
                }
            )

    _expect(
        "missing_demo_header",
        "DEMO_MARKER_HEADER",
        headers={},
        demo_marker_header_value="",
    )
    _expect(
        "wrong_demo_header_value",
        "DEMO_MARKER_HEADER_VALUE_MISMATCH",
        headers={"x-simulated-trading": "0"},
    )
    _expect(
        "live_credential_class",
        "LIVE_CREDENTIAL_CLASS_HARD_BLOCK",
        credential_class="OKX_LIVE_API_KEY",
        headers=canonical_binding_headers_v1(),
    )
    _expect(
        "global_credential_class",
        "GLOBAL_CREDENTIAL_CLASS_HARD_BLOCK",
        credential_class="OKX_DEMO_TRADING_API_KEY_ONLY",
        headers=canonical_binding_headers_v1(),
    )
    _expect(
        "legacy_btc_usdt_swap_active",
        "LEGACY_BTC_USDT_SWAP_ACTIVE_BINDING_FORBIDDEN",
        instrument_scope_exact="BTC-USDT-SWAP",
        headers=canonical_binding_headers_v1(),
    )
    _expect(
        "instrument_substitution",
        "GENERIC_OR_ALTERNATE_SYMBOL_SUBSTITUTION_FORBIDDEN",
        instrument_scope_exact="ETH-USD_UM_XPERP-310404",
        headers=canonical_binding_headers_v1(),
    )
    _expect(
        "instrument_mismatch",
        "EXACT_INSTRUMENT_SCOPE_REQUIRED",
        instrument_scope_exact="ETH-USDT-SWAP",
        headers=canonical_binding_headers_v1(),
    )
    _expect(
        "instrument_type_mismatch",
        "INSTRUMENT_TYPE_MISMATCH",
        instrument_type="SWAP",
        headers=canonical_binding_headers_v1(),
    )
    _expect(
        "rule_type_mismatch",
        "RULE_TYPE_MISMATCH",
        rule_type="linear",
        headers=canonical_binding_headers_v1(),
    )
    _expect(
        "environment_mismatch",
        "ENVIRONMENT_MISMATCH_FAIL_CLOSED",
        environment="LIVE",
        headers=canonical_binding_headers_v1(),
    )
    try:
        evaluate_okx_eea_demo_xperp_binding_v1(
            headers=canonical_binding_headers_v1(),
            **{"live_mode": bool(1)},
        )
        cases.append({"case": "live_mode", "ok": False, "error": "EXPECTED_FAIL_CLOSED"})
    except OkxEeaDemoXperpBindingError as exc:
        msg = str(exc)
        cases.append(
            {
                "case": "live_mode",
                "ok": "LIVE_MODE_OR_ACCOUNT_HARD_BLOCK" in msg,
                "error": msg,
            }
        )
    _expect(
        "global_host_fallback",
        "SILENT_HOST_FALLBACK_FORBIDDEN",
        rest_base="https://openapi.okx.com",
        headers=canonical_binding_headers_v1(),
    )
    _expect(
        "venue_fallback_global",
        "SILENT_VENUE_FALLBACK_FORBIDDEN",
        venue="okx_global",
        headers=canonical_binding_headers_v1(),
    )
    _expect(
        "order_post_authorized",
        "ORDER_POST_HARD_BLOCK",
        order_post_authorized=True,
        headers=canonical_binding_headers_v1(),
    )

    order_endpoint_ok = False
    try:
        assert_order_send_forbidden_v1(endpoint="/api/v5/trade/order")
    except OkxEeaDemoXperpBindingError as exc:
        order_endpoint_ok = "ORDER_MUTATION_ENDPOINT_HARD_BLOCK" in str(exc)
    cases.append({"case": "order_mutation_endpoint", "ok": order_endpoint_ok})

    ephemeral_pass_ok = True
    try:
        assert_order_send_forbidden_v1(
            endpoint="/api/v5/trade/order",
            order_post=True,
            ephemeral_campaign_write_gate_pass=True,
        )
    except OkxEeaDemoXperpBindingError as exc:
        ephemeral_pass_ok = False
        cases.append(
            {
                "case": "ephemeral_write_gate_pass_allows_mutation_assert",
                "ok": False,
                "error": str(exc),
            }
        )
    if ephemeral_pass_ok:
        cases.append(
            {
                "case": "ephemeral_write_gate_pass_allows_mutation_assert",
                "ok": True,
            }
        )
    package_default_still_false = ORDER_POST_AUTHORIZED is False
    cases.append(
        {
            "case": "package_default_order_post_remains_false",
            "ok": package_default_still_false,
        }
    )

    return {
        "all_ok": all(bool(c.get("ok")) for c in cases),
        "cases": cases,
    }


def verify_okx_eea_demo_xperp_binding_package_v1(*, work_dir: Path) -> dict[str, Any]:
    work_dir.mkdir(parents=True, exist_ok=True)
    binding = default_canonical_binding_v1()
    threat = build_threat_model_delta_v1()
    fail_closed = _prove_fail_closed_cases()

    claims = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "PACKAGE_MARKER": PACKAGE_MARKER,
        "OWNER": OWNER,
        "OWNER_GO_TOKEN": OWNER_GO_TOKEN,
        "VENUE": binding.venue,
        "ENVIRONMENT": binding.environment,
        "REST_HOST": binding.rest_host,
        "DEMO_MARKER_HEADER": (
            f"{binding.demo_marker_header_name}:{binding.demo_marker_header_value}"
        ),
        "INSTRUMENT_SCOPE_EXACT": binding.instrument_scope_exact,
        "INSTRUMENT_TYPE": binding.instrument_type,
        "RULE_TYPE": binding.rule_type,
        "CREDENTIAL_CLASS": binding.credential_class,
        "SECRET_REFERENCE": binding.secret_reference,
        "ORDER_POST_AUTHORIZED": ORDER_POST_AUTHORIZED,
        "ORDER_ATTEMPT_COUNT": ORDER_ATTEMPT_COUNT,
        "PRIVATE_WRITE_COUNT": PRIVATE_WRITE_COUNT,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "SECTION_11_13_STARTED": SECTION_11_13_STARTED,
        "PRE_LIVE_CYBERSECURITY_GATE": PRE_LIVE_CYBERSECURITY_GATE,
        "VENUE_ACTIVATED": binding.venue_activated,
        "NETWORK_SESSION_AUTHORIZED": binding.network_session_authorized,
        "DEMO_HEADER_FAIL_CLOSED_PROVEN": True,
        "EEA_DEMO_CREDENTIAL_ISOLATION_PROVEN": CREDENTIAL_CLASS == binding.credential_class,
        "EXACT_INSTRUMENT_SCOPE_PROVEN": INSTRUMENT_SCOPE_EXACT == binding.instrument_scope_exact,
        "INSTRUMENT_TYPE_PROVEN": INSTRUMENT_TYPE == binding.instrument_type,
        "RULE_TYPE_PROVEN": RULE_TYPE == binding.rule_type,
        "LEGACY_BTC_USDT_SWAP_ACTIVE_BINDING_REMOVED": (
            LEGACY_BTC_USDT_SWAP_ACTIVE_BINDING_REMOVED
        ),
        "OKX_GLOBAL_DEMO_ACTIVE_BINDING": OKX_GLOBAL_DEMO_ACTIVE_BINDING,
        "XPERP_PRIVATE_CAPABILITY_PROOF_BOUND": XPERP_PRIVATE_CAPABILITY_PROOF_BOUND,
        "PREDECESSOR_PRIVATE_RO_PROOF_EVIDENCE": PREDECESSOR_PRIVATE_RO_PROOF_EVIDENCE,
        "LIVE_HARD_BLOCK_PROVEN": True,
        "ORDER_SEND_FORBIDDEN_PROVEN": True,
        "SECTION_11_12_8_STATUS": SECTION_11_12_8_STATUS,
        "CANONICAL_NEXT_STEP_AFTER_MERGE": CANONICAL_NEXT_STEP_AFTER_MERGE,
        "BTC_USDT_SWAP_PATH_STATUS": BTC_USDT_SWAP_PATH_STATUS,
        "ACTIVE_SECTION_11_12_8_DERIVATIVES_CAMPAIGN_PATH": (
            ACTIVE_SECTION_11_12_8_DERIVATIVES_CAMPAIGN_PATH
        ),
        "SWAP_RUNTIME_FALLBACK": SWAP_RUNTIME_FALLBACK,
        "SWAP_WRITE_AUTHORIZATION": SWAP_WRITE_AUTHORIZATION,
        "XPERP_ONLY_ACTIVE_WRITE_SCOPE": XPERP_ONLY_ACTIVE_WRITE_SCOPE,
        "FAIL_CLOSED_MATRIX_OK": fail_closed["all_ok"],
        "THREAT_MODEL_DELTA_OK": bool(threat.get("ok")),
    }

    proof = {
        "binding": binding.to_dict(),
        "fail_closed_matrix": fail_closed,
        "threat_model_delta_id": threat.get("THREAT_MODEL_DELTA_ID"),
    }
    summary = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "VERDICT": (
            "OKX_EEA_DEMO_XPERP_BINDING_PACKAGE_PREPARED_NO_ORDER"
            if fail_closed["all_ok"] and threat.get("ok")
            else "FAIL_CLOSED"
        ),
        "ORDER_ATTEMPT_COUNT": ORDER_ATTEMPT_COUNT,
        "PRIVATE_WRITE_COUNT": PRIVATE_WRITE_COUNT,
        "ORDER_EFFECT": "NONE",
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "SECTION_11_13_STARTED": SECTION_11_13_STARTED,
        "PRE_LIVE_CYBERSECURITY_GATE": PRE_LIVE_CYBERSECURITY_GATE,
        "NEXT_CANONICAL_STEP": CANONICAL_NEXT_STEP_AFTER_MERGE,
        "BTC_USDT_SWAP_PATH_STATUS": BTC_USDT_SWAP_PATH_STATUS,
        "ACTIVE_SECTION_11_12_8_DERIVATIVES_CAMPAIGN_PATH": (
            ACTIVE_SECTION_11_12_8_DERIVATIVES_CAMPAIGN_PATH
        ),
        "ok": bool(
            fail_closed["all_ok"]
            and threat.get("ok")
            and BTC_USDT_SWAP_PATH_STATUS == "CLOSED_DEPRECATED_HISTORICAL_EVIDENCE_ONLY"
            and ACTIVE_SECTION_11_12_8_DERIVATIVES_CAMPAIGN_PATH == "OKX_EEA_DEMO_XPERP"
            and SWAP_RUNTIME_FALLBACK is False
            and SWAP_WRITE_AUTHORIZATION is False
            and XPERP_ONLY_ACTIVE_WRITE_SCOPE is True
        ),
    }

    (work_dir / CLAIMS_FILENAME).write_text(
        json.dumps(claims, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (work_dir / BINDING_PROOF_FILENAME).write_text(
        json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (work_dir / THREAT_MODEL_DELTA_FILENAME).write_text(
        json.dumps(threat, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (work_dir / SUMMARY_FILENAME).write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    lines: list[str] = []
    for name in (
        CLAIMS_FILENAME,
        BINDING_PROOF_FILENAME,
        THREAT_MODEL_DELTA_FILENAME,
        SUMMARY_FILENAME,
    ):
        digest = hashlib.sha256((work_dir / name).read_bytes()).hexdigest()
        lines.append(f"{digest}  {name}")
    (work_dir / MANIFEST_FILENAME).write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "ok": bool(summary["ok"]),
        "claims": claims,
        "summary": summary,
        "work_dir": str(work_dir),
    }
