"""Owner Flatten issuance producer/verifier tests. No live POST. No network."""

from __future__ import annotations

import json
from pathlib import Path

from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    AUTHORITY_ID_FIELDS,
    AUTHORITY_SOURCE_CANONICAL_OWNER_ISSUANCE,
    BOUND_FROZEN_ENVELOPE_ID,
    BOUND_FROZEN_EVIDENCE_RELATIVE,
    BOUND_ORIGIN_MAIN_SHA,
    FLATTEN_CONFIRM_TOKEN_EXPECTED,
    HISTORICAL_BOUND_ENVELOPE_ID,
    HISTORICAL_BOUND_ORIGIN_MAIN_SHA,
    INSTRUMENT_ID,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.contract_v1 import (
    evaluate_flatten_go_candidate_v1,
    flatten_go_contract_schema_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.durable_consume_v1 import (
    persist_flatten_durable_consume_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.execution_harness_v1 import (
    run_flatten_execution_harness_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.issuance_v1 import (
    current_section_11_14_issuance_explicit_v1,
    flatten_authority_id_v1,
    issue_owner_flatten_authority_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_transport_adapter_v1 import (
    construct_productive_flatten_submit_adapter_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)

ISSUED_AT = "2026-09-08T01:10:00.000000Z"
FROZEN_ROOT = Path(BOUND_FROZEN_EVIDENCE_RELATIVE)
HISTORICAL_ISSUANCE_ROOT = Path(
    "evidence/ops/section_11_14_current_sui_xperp_pos_1_flatten_authority_"
    "and_pre_execution_repair_v1/20260908T011645Z_canonical_owner_issuance_repair"
)
EVAL_BIND = dict(
    origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
    instrument_id=INSTRUMENT_ID,
    expected_signed_position="1",
    order_side="SELL",
    order_qty="1",
    exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
)


class NetworkTrapTransport:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def post(self, *, endpoint: str, body: dict) -> dict:
        self.calls.append({"endpoint": endpoint, "body": dict(body)})
        raise AssertionError("NETWORK_SEND_MUST_NOT_OCCUR")


def _artifact() -> dict:
    produced = issue_owner_flatten_authority_v1(
        explicit=current_section_11_14_issuance_explicit_v1(issued_at=ISSUED_AT)
    )
    assert produced["issued"] is True
    assert produced["artifact"] is not None
    return dict(produced["artifact"])


def _evaluate(*, candidate=None, issuance=None, durable_consumed_authority_id: str = ""):
    return evaluate_flatten_go_candidate_v1(
        candidate=candidate,
        issuance=issuance,
        durable_consumed_authority_id=durable_consumed_authority_id,
        **EVAL_BIND,
    )


def _frozen_envelope() -> dict:
    return json.loads((FROZEN_ROOT / "FLATTEN_ENVELOPE.json").read_text(encoding="utf-8"))


def test_schema_evaluator_is_not_issuer() -> None:
    schema = flatten_go_contract_schema_v1()
    assert schema["ISSUED"] is False
    assert schema["EVALUATOR_IS_NOT_ISSUER"] is True
    assert schema["CHAT_IS_NOT_AUTHORITY"] is True
    assert schema["ENV_IS_NOT_AUTHORITY"] is True
    assert schema["CLI_FLAG_IS_NOT_AUTHORITY"] is True


def test_no_issuance_artifact_runtime_issued_false() -> None:
    verdict = _evaluate(candidate=None, issuance=None)
    assert verdict["issued"] is False
    assert verdict["EVALUATOR_IS_NOT_ISSUER"] is True


def test_declared_go_only_runtime_issued_false() -> None:
    envelope = _frozen_envelope()
    declared = {
        "action": "FLATTEN_EXISTING_POSITION",
        "section": "11.14",
        "purpose": "SECTION_11_14_FLATTEN_EXISTING_POSITION",
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
        "OWNER_GO_DECLARED": True,
    }
    verdict = _evaluate(candidate=declared, issuance=None)
    assert verdict["accepted"] is True
    assert verdict["issued"] is False


def test_issued_false_runtime_issued_false() -> None:
    artifact = _artifact()
    artifact["issued"] = False
    verdict = _evaluate(candidate=artifact, issuance=artifact)
    assert verdict["issued"] is False
    assert "ISSUANCE_ARTIFACT_NOT_ISSUED" in verdict["reasons"]


def test_wrong_authority_source_runtime_issued_false() -> None:
    artifact = _artifact()
    artifact["authority_source"] = "CHAT_DECLARATION"
    verdict = _evaluate(candidate=artifact, issuance=artifact)
    assert verdict["issued"] is False
    assert "ISSUANCE_AUTHORITY_SOURCE_FORBIDDEN" in verdict["reasons"]


def test_missing_required_field_runtime_issued_false() -> None:
    artifact = _artifact()
    del artifact["section"]
    verdict = _evaluate(candidate=artifact, issuance=artifact)
    assert verdict["issued"] is False
    assert any("ISSUANCE_FIELDS_MISSING" in str(item) for item in verdict["reasons"])


def test_wrong_sha_runtime_issued_false() -> None:
    artifact = _artifact()
    artifact["origin_main_sha"] = "0" * 40
    verdict = _evaluate(candidate=artifact, issuance=artifact)
    assert verdict["issued"] is False
    assert "ISSUANCE_SHA_MISMATCH" in verdict["reasons"]


def test_wrong_envelope_runtime_issued_false() -> None:
    artifact = _artifact()
    artifact["exact_envelope_id"] = "ab" * 32
    verdict = _evaluate(candidate=artifact, issuance=artifact)
    assert verdict["issued"] is False
    assert "ISSUANCE_ENVELOPE_MISMATCH" in verdict["reasons"]


def test_wrong_section_runtime_issued_false() -> None:
    artifact = _artifact()
    artifact["section"] = "11.13.5"
    verdict = _evaluate(candidate=artifact, issuance=artifact)
    assert verdict["issued"] is False
    assert "ISSUANCE_SECTION_MISMATCH" in verdict["reasons"]


def test_consumed_true_runtime_issued_false() -> None:
    artifact = _artifact()
    artifact["consumed"] = True
    verdict = _evaluate(candidate=artifact, issuance=artifact)
    assert verdict["issued"] is False
    assert "ISSUANCE_CONSUMED" in verdict["reasons"]


def test_single_use_false_runtime_issued_false() -> None:
    artifact = _artifact()
    artifact["single_use"] = False
    verdict = _evaluate(candidate=artifact, issuance=artifact)
    assert verdict["issued"] is False
    assert "ISSUANCE_SINGLE_USE_REQUIRED" in verdict["reasons"]


def test_retry_allowed_true_runtime_issued_false() -> None:
    artifact = _artifact()
    artifact["retry_allowed"] = True
    verdict = _evaluate(candidate=artifact, issuance=artifact)
    assert verdict["issued"] is False
    assert "ISSUANCE_RETRY_MUST_BE_FALSE" in verdict["reasons"]


def test_second_submit_allowed_true_runtime_issued_false() -> None:
    artifact = _artifact()
    artifact["second_submit_allowed"] = True
    verdict = _evaluate(candidate=artifact, issuance=artifact)
    assert verdict["issued"] is False
    assert "ISSUANCE_SECOND_SUBMIT_MUST_BE_FALSE" in verdict["reasons"]


def test_wrong_confirm_token_runtime_issued_false() -> None:
    artifact = _artifact()
    artifact["confirm_token"] = "NO"
    verdict = _evaluate(candidate=artifact, issuance=artifact)
    assert verdict["issued"] is False
    assert "ISSUANCE_CONFIRM_TOKEN_MISMATCH" in verdict["reasons"]


def test_valid_full_canonical_issuance_runtime_issued_true() -> None:
    artifact = _artifact()
    verdict = _evaluate(candidate=artifact, issuance=artifact)
    assert verdict["accepted"] is True
    assert verdict["issued"] is True
    assert verdict["EVALUATOR_IS_NOT_ISSUER"] is True
    assert verdict["authority_source"] == AUTHORITY_SOURCE_CANONICAL_OWNER_ISSUANCE
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert POST_ALLOWED is False


def test_same_authority_after_durable_consume_runtime_issued_false(tmp_path: Path) -> None:
    artifact = _artifact()
    persist_flatten_durable_consume_v1(
        store_root=tmp_path,
        envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        durable_state="COMPLETED",
        post_count=1,
        outcome="FAKE_POST_OK",
        authority_id=str(artifact["authority_id"]),
    )
    verdict = _evaluate(
        candidate=artifact,
        issuance=artifact,
        durable_consumed_authority_id=str(artifact["authority_id"]),
    )
    assert verdict["issued"] is False
    assert "ISSUANCE_DURABLE_CONSUMED" in verdict["reasons"]


def test_authority_id_deterministic() -> None:
    first = _artifact()
    second = _artifact()
    assert first["authority_id"] == second["authority_id"]
    assert first["authority_id"] == flatten_authority_id_v1(first)
    assert set(AUTHORITY_ID_FIELDS).issubset(first)


def test_identity_field_mutation_changes_authority_id() -> None:
    artifact = _artifact()
    original = artifact["authority_id"]
    mutated = dict(artifact)
    mutated["instrument_id"] = "BTC-USD_UM_XPERP-1"
    assert flatten_authority_id_v1(mutated) != original


def test_serialization_roundtrip_preserves_identity() -> None:
    artifact = _artifact()
    restored = json.loads(json.dumps(artifact, sort_keys=True))
    assert flatten_authority_id_v1(restored) == artifact["authority_id"]
    assert restored["authority_id"] == artifact["authority_id"]


def test_valid_issued_session_unarmed_zero_post() -> None:
    artifact = _artifact()
    envelope = _frozen_envelope()
    trap = NetworkTrapTransport()
    result = run_flatten_execution_harness_v1(
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        candidate=artifact,
        envelope=envelope,
        issuance=artifact,
        mode="execute",
        session_armed=False,
        capture_wired=True,
        transport=trap,
        frozen_evidence_root=str(FROZEN_ROOT),
    )
    assert trap.calls == []
    assert result["POST_COUNT"] == 0
    assert result["REAL_POST_COUNT"] == 0
    assert result["WIRE_SEND"] is False
    assert result["AUTHORITY_CANDIDATE_ACCEPTED"] is True
    assert result["AUTHORITY_RUNTIME_ISSUED"] is True
    assert result["SESSION_ARMED"] is False
    assert result["NETWORK_SESSION_AUTHORIZED"] is False
    assert "SESSION_NOT_ARMED" in result["reasons"]


def test_valid_issued_transport_unbound_zero_post() -> None:
    artifact = _artifact()
    envelope = _frozen_envelope()
    result = run_flatten_execution_harness_v1(
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        candidate=artifact,
        envelope=envelope,
        issuance=artifact,
        mode="execute",
        session_armed=True,
        capture_wired=True,
        transport=None,
        frozen_evidence_root=str(FROZEN_ROOT),
    )
    assert result["POST_COUNT"] == 0
    assert result["REAL_POST_COUNT"] == 0
    assert result["WIRE_SEND"] is False
    assert result["AUTHORITY_RUNTIME_ISSUED"] is True
    assert "PRODUCTIVE_TRANSPORT_NOT_BOUND" in result["reasons"]


def test_valid_issued_network_session_unauthorized_zero_post() -> None:
    artifact = _artifact()
    envelope = _frozen_envelope()
    adapter = construct_productive_flatten_submit_adapter_v1()
    assert adapter.inner.network_session_authorized is False
    trap = NetworkTrapTransport()
    result = run_flatten_execution_harness_v1(
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        candidate=artifact,
        envelope=envelope,
        issuance=artifact,
        mode="execute",
        session_armed=True,
        capture_wired=True,
        transport=trap,
        frozen_evidence_root=str(FROZEN_ROOT),
    )
    assert trap.calls == []
    assert result["POST_COUNT"] == 0
    assert result["REAL_POST_COUNT"] == 0
    assert result["WIRE_SEND"] is False
    assert result["NETWORK_SESSION_AUTHORIZED"] is False
    assert adapter.inner.network_session_authorized is False


def test_producer_rejects_self_attested_issued() -> None:
    explicit = current_section_11_14_issuance_explicit_v1(issued_at=ISSUED_AT)
    explicit["issued"] = True
    produced = issue_owner_flatten_authority_v1(explicit=explicit)
    assert produced["issued"] is False
    assert "ISSUANCE_INPUT_MUST_NOT_SELF_ATTEST_ISSUED" in produced["reasons"]


def test_producer_rejects_missing_field() -> None:
    explicit = current_section_11_14_issuance_explicit_v1(issued_at=ISSUED_AT)
    del explicit["confirm_token"]
    produced = issue_owner_flatten_authority_v1(explicit=explicit)
    assert produced["issued"] is False
    assert produced["artifact"] is None


def test_historical_persisted_issuance_is_not_current_submit_grant() -> None:
    artifact = json.loads(
        (HISTORICAL_ISSUANCE_ROOT / "OWNER_ISSUANCE_ARTIFACT.json").read_text(encoding="utf-8")
    )
    assert artifact["issued"] is True
    assert artifact["origin_main_sha"] == HISTORICAL_BOUND_ORIGIN_MAIN_SHA
    assert artifact["exact_envelope_id"] == HISTORICAL_BOUND_ENVELOPE_ID
    assert artifact["authority_id"] == (
        "2c2c228866e6cbfe5aa23ecafe4eec7c747cba230b95057ee2206c2a52bf8041"
    )
    verdict = _evaluate(candidate=artifact, issuance=artifact)
    assert verdict["accepted"] is False
    assert verdict["issued"] is False
    assert "ISSUANCE_SHA_MISMATCH" in verdict["reasons"]
    assert "ISSUANCE_ENVELOPE_MISMATCH" in verdict["reasons"]
    assert artifact["exact_envelope_id"] != BOUND_FROZEN_ENVELOPE_ID
    assert artifact["origin_main_sha"] != BOUND_ORIGIN_MAIN_SHA


def test_producer_rejects_historical_sha_and_envelope() -> None:
    explicit = current_section_11_14_issuance_explicit_v1(issued_at=ISSUED_AT)
    explicit["origin_main_sha"] = HISTORICAL_BOUND_ORIGIN_MAIN_SHA
    explicit["exact_envelope_id"] = HISTORICAL_BOUND_ENVELOPE_ID
    produced = issue_owner_flatten_authority_v1(explicit=explicit)
    assert produced["issued"] is False
    assert produced["artifact"] is None
    assert "ISSUANCE_SHA_MISMATCH" in produced["reasons"]
    assert "ISSUANCE_ENVELOPE_MISMATCH" in produced["reasons"]
