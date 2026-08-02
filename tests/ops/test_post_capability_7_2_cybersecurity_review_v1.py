"""Contract: Post-Capability-7.2 cybersecurity review evidence + Truth Map guards."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.ops.single_future_stateful_no_order_runtime_activation_v1.network_boundary_v1 import (
    prove_network_credential_boundary_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.simulated_execution_port_v1 import (
    prove_execution_port_separation_v1,
    prove_no_polymorphic_real_port_switch_v1,
    refuse_real_execution_adapter_construction_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.reason_codes_v1 import (
    ActivationFailureCodeV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = REPO_ROOT / "docs" / "evidence" / "post_capability_7_2_cybersecurity_review_v1"
TRUTH_MAP = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md"


def test_post_cap72_cyber_review_manifest_and_result() -> None:
    manifest = (EVIDENCE_ROOT / "MANIFEST.sha256").read_text(encoding="utf-8")
    result_path = EVIDENCE_ROOT / "post_capability_7_2_cybersecurity_review_result_v1.json"
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    digest = hashlib.sha256(result_path.read_bytes()).hexdigest()
    assert f"{digest}  {result_path.name}" in manifest
    assert payload["CAPABILITY_ID"] == "POST_CAPABILITY_7_2_CYBERSECURITY_REVIEW_V1"
    assert payload["VERDICT"] == "PASS_NO_SECURITY_DEFECT"
    assert payload["HARD_STOP"] is False
    assert payload["CYBERSECURITY_REVIEW_CURRENT"] is True
    assert payload["NEXT_RUNTIME_RUN_ALLOWED"] is False
    assert payload["CRITICAL_SECURITY_FINDING_COUNT"] == 0
    assert payload["HIGH_SECURITY_FINDING_COUNT"] == 0
    inv = payload["SECURITY_INVARIANTS"]
    assert inv["REAL_EXECUTION_ADAPTER_CONSTRUCTED"] is False
    assert inv["EXCHANGE_ORDER_SUBMIT_REACHABLE"] is False
    assert inv["EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"] is False
    assert inv["PRIVATE_ENDPOINT_REACHABLE"] is False
    assert inv["AUTH_HEADER_PRESENT"] is False
    assert inv["HTTP_METHOD_ALLOWLIST_GET_ONLY"] is True
    assert inv["NETWORK_ALLOWLIST_PUBLIC_MARKET_DATA_ONLY"] is True
    assert inv["SIMULATED_EXECUTION_PORT_SEPARATE_FROM_REAL_EXECUTION_PORT"] is True
    assert inv["NO_REAL_SUBMIT_ORDER_INTERFACE_IN_NO_ORDER_HOST"] is True
    assert inv["NOTION_RUNTIME_AUTHORITY"] is False
    assert inv["NOTION_TRADING_AUTHORITY"] is False


def test_post_cap72_security_invariants_recompute() -> None:
    net = prove_network_credential_boundary_v1()
    port = prove_execution_port_separation_v1()
    poly = prove_no_polymorphic_real_port_switch_v1()
    assert net["ok"] is True
    assert port["ok"] is True
    assert poly["ok"] is True
    assert net["PRIVATE_ENDPOINT_REACHABLE"] is False
    assert net["AUTH_HEADER_PRESENT"] is False
    assert net["HTTP_METHOD_ALLOWLIST_GET_ONLY"] is True
    assert port["REAL_EXECUTION_ADAPTER_CONSTRUCTED"] is False
    assert port["EXCHANGE_ORDER_SUBMIT_REACHABLE"] is False
    assert port["NO_REAL_SUBMIT_ORDER_INTERFACE_IN_NO_ORDER_HOST"] is True
    try:
        refuse_real_execution_adapter_construction_v1()
        raise AssertionError("real adapter construction must fail closed")
    except Exception as exc:  # noqa: BLE001 — negative control
        assert ActivationFailureCodeV1.REAL_EXECUTION_REACHABLE.value in str(exc)


def test_truth_map_cybersecurity_review_current_without_runtime_run() -> None:
    text = TRUTH_MAP.read_text(encoding="utf-8")
    assert "CYBERSECURITY_REVIEW_CURRENT=true" in text
    assert "NEXT_RUNTIME_RUN_ALLOWED=false" in text
    assert "NOTION_REPOSITORY_MIRROR_CURRENT=true" in text
    # Authority remains documentary; live/order barriers preserved.
    assert "LIVE_ORDERS=false" in text
    assert "EXCHANGE_CREDENTIAL_USE=false" in text
    assert "PUBLIC_MD_NETWORK_SESSION_OBSERVED=false" in text
    assert "POST_CAPABILITY_7_2_CYBERSECURITY_REVIEW_V1" in text
