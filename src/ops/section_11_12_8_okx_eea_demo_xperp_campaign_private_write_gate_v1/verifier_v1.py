"""Offline verifier for ephemeral XPerp campaign private-write gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.ops.section_11_12_8_okx_eea_demo_xperp_campaign_private_write_gate_v1.constants_v1 import (
    CANONICAL_NEXT_STEP_AFTER_MERGE,
    CANONICAL_ORDER_SZ,
    CAPABILITY_ID,
    CLAIMS_FILENAME,
    INSTRUMENT_SCOPE_EXACT,
    LIVE_AUTHORIZED,
    MANIFEST_FILENAME,
    OWNER,
    PACKAGE_DEFAULT_ORDER_POST_AUTHORIZED,
    PACKAGE_MARKER,
    PRE_LIVE_CYBERSECURITY_GATE,
    REST_BASE,
    SECTION_11_12_8_STATUS,
    SECTION_11_13_STARTED,
    SUMMARY_FILENAME,
    VENUE,
)
from src.ops.section_11_12_8_okx_eea_demo_xperp_campaign_private_write_gate_v1.gate_v1 import (
    OkxEeaDemoXperpCampaignPrivateWriteGateError,
    assert_mutation_allowed_under_ephemeral_gate_v1,
    evaluate_ephemeral_campaign_private_write_gate_v1,
)
from src.ops.section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1.constants_v1 import (
    ORDER_POST_AUTHORIZED as BINDING_ORDER_POST_AUTHORIZED,
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _seal_manifest(work_dir: Path) -> None:
    lines: list[str] = []
    for path in sorted(work_dir.rglob("*")):
        if not path.is_file() or path.name == MANIFEST_FILENAME:
            continue
        rel = path.relative_to(work_dir).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {rel}")
    (work_dir / MANIFEST_FILENAME).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _fail_closed_matrix() -> list[dict[str, Any]]:
    base = dict(
        owner_go_consumed=True,
        owner_go_scope="EXECUTE_BOUNDED_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_CAMPAIGN",
        owner_go_authorization="EXECUTE_BOUNDED_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_CAMPAIGN",
        confirm_latched=True,
        testnet_authorized_runtime=True,
        campaign_enabled=True,
        campaign_armed=True,
        risk_gate_pass=True,
        kill_switch_pass=True,
        emergency_control_pass=True,
        account_binding_pass=True,
        endpoint_allowlist_pass=True,
        bound_client_pass=True,
        secretref_ephemeral_loaded=True,
        headers={"x-simulated-trading": "1"},
    )
    cases: list[dict[str, Any]] = []

    def _expect(name: str, match: str, **overrides: Any) -> None:
        kwargs = dict(base)
        kwargs.update(overrides)
        try:
            evaluate_ephemeral_campaign_private_write_gate_v1(**kwargs)
            cases.append({"case": name, "ok": False, "error": "EXPECTED_FAIL_CLOSED"})
        except OkxEeaDemoXperpCampaignPrivateWriteGateError as exc:
            cases.append({"case": name, "ok": match in str(exc), "error": str(exc)})

    _expect("missing_confirm", "HIDDEN_CONFIRM_NOT_LATCHED", confirm_latched=False)
    _expect("missing_secretref", "SECRETREF_EPHEMERAL_NOT_LOADED", secretref_ephemeral_loaded=False)
    _expect("live_true", "LIVE_PATH_HARD_BLOCK", live_authorized=True)
    _expect("wrong_venue", "VENUE_MISMATCH", venue="okx_global")
    _expect("wrong_host", "HOST_NOT_OKX_EEA_DEMO", rest_base="https://openapi.okx.com")
    _expect(
        "wrong_instrument",
        "INSTRUMENT_SCOPE_MISMATCH",
        instrument_scope_exact="BTC-USDT-SWAP",
    )
    _expect(
        "wrong_go",
        "OWNER_GO_SCOPE_MISMATCH",
        owner_go_scope="SOME_OTHER_GO",
        owner_go_authorization="SOME_OTHER_GO",
    )
    _expect(
        "package_default_true",
        "PACKAGE_DEFAULT_ORDER_POST_MUST_REMAIN_FALSE",
        package_default_order_post_authorized=True,
    )
    return cases


def verify_okx_eea_demo_xperp_campaign_private_write_gate_v1(*, work_dir: Path) -> dict[str, Any]:
    work_dir.mkdir(parents=True, exist_ok=True)
    gate = evaluate_ephemeral_campaign_private_write_gate_v1(
        owner_go_consumed=True,
        owner_go_scope="EXECUTE_BOUNDED_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_CAMPAIGN",
        owner_go_authorization="EXECUTE_BOUNDED_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_CAMPAIGN",
        confirm_latched=True,
        testnet_authorized_runtime=True,
        campaign_enabled=True,
        campaign_armed=True,
        risk_gate_pass=True,
        kill_switch_pass=True,
        emergency_control_pass=True,
        account_binding_pass=True,
        endpoint_allowlist_pass=True,
        bound_client_pass=True,
        secretref_ephemeral_loaded=True,
        headers={"x-simulated-trading": "1"},
    )
    assert_mutation_allowed_under_ephemeral_gate_v1(
        endpoint="/api/v5/trade/order",
        ephemeral_campaign_write_gate_pass=True,
    )
    mutation_blocked_without_gate = False
    try:
        assert_mutation_allowed_under_ephemeral_gate_v1(
            endpoint="/api/v5/trade/order",
            ephemeral_campaign_write_gate_pass=False,
        )
    except OkxEeaDemoXperpCampaignPrivateWriteGateError:
        mutation_blocked_without_gate = True

    fail_cases = _fail_closed_matrix()
    claims = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "PACKAGE_MARKER": PACKAGE_MARKER,
        "OWNER": OWNER,
        "PACKAGE_DEFAULT_ORDER_POST_AUTHORIZED": PACKAGE_DEFAULT_ORDER_POST_AUTHORIZED,
        "BINDING_PACKAGE_ORDER_POST_AUTHORIZED": BINDING_ORDER_POST_AUTHORIZED,
        "VENUE": VENUE,
        "REST_BASE": REST_BASE,
        "INSTRUMENT_SCOPE_EXACT": INSTRUMENT_SCOPE_EXACT,
        "CANONICAL_ORDER_SZ": CANONICAL_ORDER_SZ,
        "SECTION_11_12_8_STATUS": SECTION_11_12_8_STATUS,
        "CANONICAL_NEXT_STEP_AFTER_MERGE": CANONICAL_NEXT_STEP_AFTER_MERGE,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "SECTION_11_13_STARTED": SECTION_11_13_STARTED,
        "PRE_LIVE_CYBERSECURITY_GATE": PRE_LIVE_CYBERSECURITY_GATE,
        "NETWORK_EFFECT": "NONE",
        "ORDER_EFFECT": "NONE",
        "ORDER_ATTEMPT_COUNT": 0,
    }
    summary = {
        "ok": bool(gate.pass_gate)
        and mutation_blocked_without_gate
        and all(c["ok"] for c in fail_cases)
        and PACKAGE_DEFAULT_ORDER_POST_AUTHORIZED is False
        and BINDING_ORDER_POST_AUTHORIZED is False,
        "ephemeral_campaign_write_gate_pass": gate.ephemeral_campaign_write_gate_pass,
        "mutation_blocked_without_gate": mutation_blocked_without_gate,
        "fail_closed_cases": fail_cases,
        "ORDER_EFFECT": "NONE",
        "LIVE_AUTHORIZED": False,
        "SECTION_11_13_STARTED": False,
    }
    _write_json(work_dir / CLAIMS_FILENAME, claims)
    _write_json(work_dir / SUMMARY_FILENAME, summary)
    _write_json(work_dir / "GATE_PROOF.json", gate.to_dict())
    _seal_manifest(work_dir)
    return {"ok": summary["ok"], "summary": summary, "claims": claims, "gate": gate.to_dict()}
