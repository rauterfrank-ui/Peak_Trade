"""Offline fail-closed tests for the §11.14 wire-send Owner contract spec.

No live GET. No live POST. No session arming. No durable consume. No mint of
OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1.
"""

from __future__ import annotations

import json
import socket
import urllib.request
from pathlib import Path

import pytest

from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    AUTHORITY_TYPE_OWNER_FLATTEN_ISSUANCE,
    AUTHORITY_TYPE_OWNER_NETWORK_SESSION,
    BOUND_FROZEN_ENVELOPE_ID,
    BOUND_FROZEN_EVIDENCE_RELATIVE,
    BOUND_ORIGIN_MAIN_SHA,
    FLATTEN_ACTION,
    FLATTEN_CONFIRM_TOKEN_EXPECTED,
    FLATTEN_HTTP_ENDPOINT,
    FLATTEN_PURPOSE_EXPECTED,
    FLATTEN_SECTION,
    INSTRUMENT_ID,
    NETWORK_SESSION_CONFIRM_TOKEN_EXPECTED,
    PRODUCTIVE_TRANSPORT_BIND_KIND_NO_SEND,
    SESSION_ARMING_STANDING,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.execution_harness_v1 import (
    run_flatten_execution_harness_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.issuance_v1 import (
    current_section_11_14_issuance_explicit_v1,
    issue_owner_flatten_authority_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.network_session_authority_v1 import (
    current_section_11_14_network_session_explicit_v1,
    issue_owner_network_session_authority_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_transport_adapter_v1 import (
    FlattenProductiveTransportAdapterError,
    construct_productive_flatten_submit_adapter_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_transport_bind_v1 import (
    prepare_productive_flatten_transport_bind_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_wire_send_owner_contract_schema_v1 import (
    AUTHORITY_TYPE_OWNER_PRODUCTIVE_WIRE_SEND,
    PRODUCER_IMPLEMENTED,
    PRODUCER_SYMBOL_ABSENT,
    PRODUCTIVE_WIRE_SEND_CONFIRM_TOKEN_EXPECTED,
    PROPOSED_ORCHESTRATOR_SYMBOL,
    PROPOSED_SEND_CAPABLE_BIND_SYMBOL,
    productive_wire_send_owner_contract_schema_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE = (
    REPO_ROOT
    / "src/ops/section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1"
)
SCHEMA_PATH = PACKAGE / "productive_wire_send_owner_contract_schema_v1.py"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/SECTION_11_14_PRODUCTIVE_WIRE_SEND_OWNER_CONTRACT_AND_ORCHESTRATOR_SPEC_V1.md"
)
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
FROZEN_ROOT = Path(BOUND_FROZEN_EVIDENCE_RELATIVE)


def _boom(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("REAL_NETWORK_MUST_NOT_OCCUR")


def _frozen_envelope() -> dict:
    return json.loads((FROZEN_ROOT / "FLATTEN_ENVELOPE.json").read_text(encoding="utf-8"))


def _candidate(*, envelope: dict) -> dict:
    return {
        "action": FLATTEN_ACTION,
        "section": FLATTEN_SECTION,
        "purpose": FLATTEN_PURPOSE_EXPECTED,
        "confirm_token": FLATTEN_CONFIRM_TOKEN_EXPECTED,
        "origin_main_sha": BOUND_ORIGIN_MAIN_SHA,
        "instrument_id": INSTRUMENT_ID,
        "expected_signed_position": "1",
        "pos_side": "net",
        "margin_mode": "cross",
        "order_side": "SELL",
        "order_qty": "1",
        "order_qty_unit": "CONTRACTS_SZ",
        "reduce_only": True,
        "order_type": "LIMIT",
        "exact_envelope_id": envelope["FLATTEN_ENVELOPE_ID"],
        "single_use": True,
        "retry_allowed": False,
        "second_submit_allowed": False,
        "pre_submit_fresh_get_required": True,
        "post_submit_position_recon_required": True,
        "capture_required": True,
        "consumed": False,
        "venue_reduce_only_no_flip_acknowledgement": "UNPROVEN",
    }


def _session_artifact() -> dict:
    return issue_owner_network_session_authority_v1(
        explicit=current_section_11_14_network_session_explicit_v1(issued_at="2026-09-08T05:00:00Z")
    )["artifact"]


def _flatten_artifact() -> dict:
    return issue_owner_flatten_authority_v1(
        explicit=current_section_11_14_issuance_explicit_v1(issued_at="2026-09-08T05:00:00Z")
    )["artifact"]


def test_schema_is_not_issued_and_not_a_send_grant() -> None:
    schema = productive_wire_send_owner_contract_schema_v1()
    assert schema["ISSUED"] is False
    assert schema["PRESENT"] is False
    assert schema["ACCEPTED"] is False
    assert schema["CONSUMED"] is False
    assert schema["PRODUCER_IMPLEMENTED"] is False
    assert schema["ORCHESTRATOR_IMPLEMENTED"] is False
    assert schema["SEND_CAPABLE_BIND_IMPLEMENTED"] is False
    assert schema["kind"] == AUTHORITY_TYPE_OWNER_PRODUCTIVE_WIRE_SEND
    assert schema["kind"] != AUTHORITY_TYPE_OWNER_NETWORK_SESSION
    assert schema["kind"] != AUTHORITY_TYPE_OWNER_FLATTEN_ISSUANCE
    assert schema["confirm_token_expected"] == PRODUCTIVE_WIRE_SEND_CONFIRM_TOKEN_EXPECTED
    assert schema["confirm_token_expected"] != NETWORK_SESSION_CONFIRM_TOKEN_EXPECTED
    assert schema["confirm_token_expected"] != FLATTEN_CONFIRM_TOKEN_EXPECTED
    assert schema["session_arming_standing"] is False
    assert schema["standing_live_enabled"] is False
    assert schema["ISSUING_MUST_NOT_ARM_OR_SEND"] is True
    assert schema["proposed_orchestrator_symbol"] == PROPOSED_ORCHESTRATOR_SYMBOL
    assert schema["proposed_send_capable_bind_symbol"] == PROPOSED_SEND_CAPABLE_BIND_SYMBOL
    assert schema["existing_no_send_bind_kind"] == PRODUCTIVE_TRANSPORT_BIND_KIND_NO_SEND


def test_no_wire_send_producer_exists_in_this_package() -> None:
    assert PRODUCER_IMPLEMENTED is False
    blob = "\n".join(path.read_text(encoding="utf-8") for path in PACKAGE.glob("*.py"))
    assert f"def {PRODUCER_SYMBOL_ABSENT}" not in blob


def test_new_schema_module_has_no_urllib_post() -> None:
    text = SCHEMA_PATH.read_text(encoding="utf-8")
    assert "urllib" not in text
    assert "urlopen" not in text
    assert "httpx" not in text
    assert "def issue_owner_productive_wire_send" not in text


def test_standing_predicates_remain_safe_defaults() -> None:
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert CANARY_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert SESSION_ARMING_STANDING is False


def test_session_armed_false_does_not_send(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    envelope = _frozen_envelope()
    result = run_flatten_execution_harness_v1(
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        candidate=_candidate(envelope=envelope),
        envelope=envelope,
        mode="execute",
        session_armed=False,
        issuance=_flatten_artifact(),
        productive_bind=prepare_productive_flatten_transport_bind_v1(),
        network_session=_session_artifact(),
        transport=None,
    )
    assert result["POST_COUNT"] == 0
    assert result["REAL_POST_COUNT"] == 0
    assert result["WIRE_SEND"] is False
    assert result["OWNER_TOKEN_CONSUMED"] is False
    assert result["NETWORK_SESSION_AUTHORIZED"] is False
    assert "SESSION_NOT_ARMED" in result["reasons"]


def test_issued_network_session_and_unissued_wire_send_schema_do_not_arm_or_send(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    envelope = _frozen_envelope()
    schema = productive_wire_send_owner_contract_schema_v1()
    assert schema["ISSUED"] is False
    result = run_flatten_execution_harness_v1(
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        candidate=_candidate(envelope=envelope),
        envelope=envelope,
        mode="execute",
        session_armed=True,
        issuance=_flatten_artifact(),
        productive_bind=prepare_productive_flatten_transport_bind_v1(),
        network_session=_session_artifact(),
        transport=None,
        durable_store=tmp_path,
    )
    assert result["NETWORK_SESSION_AUTHORITY_ISSUED"] is True
    assert result["NETWORK_SESSION_AUTHORIZED"] is False
    assert result["POST_COUNT"] == 0
    assert result["REAL_POST_COUNT"] == 0
    assert result["WIRE_SEND"] is False
    assert result["OWNER_TOKEN_CONSUMED"] is False
    assert "PRODUCTIVE_WIRE_SEND_NOT_IMPLEMENTED_IN_THIS_REPAIR" in result["reasons"]


def test_missing_wire_send_authority_does_not_send(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    envelope = _frozen_envelope()
    result = run_flatten_execution_harness_v1(
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        candidate=_candidate(envelope=envelope),
        envelope=envelope,
        mode="execute",
        session_armed=True,
        issuance=_flatten_artifact(),
        productive_bind=prepare_productive_flatten_transport_bind_v1(),
        network_session=_session_artifact(),
        transport=None,
    )
    assert result["WIRE_SEND"] is False
    assert result["POST_COUNT"] == 0
    assert productive_wire_send_owner_contract_schema_v1()["ISSUED"] is False
    assert "PRODUCTIVE_WIRE_SEND_NOT_IMPLEMENTED_IN_THIS_REPAIR" in result["reasons"]


def test_no_send_adapter_remains_no_send(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    adapter = construct_productive_flatten_submit_adapter_v1()
    assert adapter.inner.network_session_authorized is False
    with pytest.raises(FlattenProductiveTransportAdapterError, match="NETWORK_SESSION_NOT"):
        adapter.post(endpoint=FLATTEN_HTTP_ENDPOINT, body={"instId": INSTRUMENT_ID})
    assert adapter.calls == []
    bind = prepare_productive_flatten_transport_bind_v1()
    assert bind.kind == PRODUCTIVE_TRANSPORT_BIND_KIND_NO_SEND
    assert bind.send_permitted is False
    adapter_src = (
        REPO_ROOT
        / "src/ops/section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1"
        / "productive_transport_adapter_v1.py"
    ).read_text(encoding="utf-8")
    assert "inner.send" not in adapter_src
    assert "urlopen" not in adapter_src


def test_spec_and_runbook_persist_unissued_contract() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_SECTION_11_14_PRODUCTIVE_WIRE_SEND_OWNER_CONTRACT_AND_ORCHESTRATOR_SPEC_V1"
        in spec
    )
    assert "OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_ISSUED=false" in spec
    assert "EXISTING_SECTION_11_14_WIRE_SEND_OWNER_SCHEMA=false" in spec
    assert "PRODUCER_IMPLEMENTED=false" in spec
    assert "ORCHESTRATOR_IMPLEMENTED=false" in spec
    assert "POST_PERFORMED=false" in spec
    assert "NO_SEND_ADAPTER_SEMANTICS_CHANGED=false" in spec
    assert "11.14 PRODUCTIVE_WIRE_SEND_OWNER_CONTRACT_AND_ORCHESTRATOR_SPEC" in runbook
    assert "OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1" in runbook
    assert "ProductiveWireSendOrchestratorV1" in runbook
    assert "ProductiveTransportBindSendCapableV1" in runbook
    start = runbook.find("### 11.14 PRODUCTIVE_WIRE_SEND_OWNER_CONTRACT_AND_ORCHESTRATOR_SPEC")
    end = runbook.find("## 11.15 Full-autonomy observability and audit trail", start)
    assert start >= 0
    assert end > start
    section = runbook[start:end]
    assert "OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_ISSUED=false" in section
    assert "ORCHESTRATOR_IMPLEMENTED=false" in section
    assert "POST_PERFORMED=false" in section
    assert "WIRE_SEND_EXECUTED=false" in section
    assert "DURABLE_CONSUMED=false" in section
    historical = runbook[
        runbook.find(
            "### 11.14 CURRENT_SUI_XPERP_POS_1_FLATTEN_AUTHORITY_AND_PRE_EXECUTION_REPAIR"
        ) : start
    ]
    assert "OWNER_FLATTEN_GO_PRESENT=false" in historical
    assert "OWNER_FLATTEN_GO_PRESENT=true" not in section
